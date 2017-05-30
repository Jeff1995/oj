
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <time.h>
#include <stdarg.h>
#include <ctype.h>
#include <sys/wait.h>
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/user.h>
#include <sys/syscall.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <sys/signal.h>
#include <sys/stat.h>
#include <unistd.h>
#include <assert.h>

#ifdef __i386
int LANG_CV[256] = { 85, 8,140, SYS_time, SYS_read, SYS_uname, SYS_write, SYS_open,
	SYS_close, SYS_execve, SYS_access, SYS_brk, SYS_munmap, SYS_mprotect,
	SYS_mmap2, SYS_fstat64, SYS_set_thread_area, 252, 0 };
#else
   int LANG_CV[256] = {0,1,2,4,5,9,11,12,21,59,63,89,158,231,240, 8, SYS_time, SYS_read, SYS_uname, SYS_write, SYS_open,
		SYS_close, SYS_execve, SYS_access, SYS_brk, SYS_munmap, SYS_mprotect,
		SYS_mmap, SYS_fstat, SYS_set_thread_area, 252, SYS_arch_prctl, 231, 0 };
#endif

#ifdef __i386
#define REG_SYSCALL orig_eax
#define REG_RET eax
#define REG_ARG0 ebx
#define REG_ARG1 ecx
#else /* __i386 */
#define REG_SYSCALL orig_rax
#define REG_RET rax
#define REG_ARG0 rdi
#define REG_ARG1 rsi
#endif /* __i386 */

#define STD_MB 1048576 /* 1MB */
#define STD_F_LIM (STD_MB<<5) /* file size limit 32 MB */
#define STD_STACK_LIM (STD_MB << 6) /* stack size limit 64 MB */


int time_limit; /* time limit in secods */
int mem_limit; /* memory limit in MB */

const char* standard_input_file;
const char* output_file;
const char* error_file;
const char* work_dir;
const char* program_file;
const char* input_dir;

int userid;

#define JUDGE_AC 0
#define JUDGE_RE 1
#define JUDGE_TLE 2
#define JUDGE_MLE 3
#define JUDGE_OLE 4
#define JUDGE_RF 5

#define BUFFER_SIZE 5120

int execute_cmd(const char * fmt, ...) {
	char cmd[BUFFER_SIZE];

	int ret = 0;
	va_list ap;

	va_start(ap, fmt);
	vsprintf(cmd, fmt, ap);
	ret = system(cmd);
	va_end(ap);
	return ret;
}

int get_proc_status(int pid, const char * mark) {
    FILE * pf;
    char fn[BUFFER_SIZE], buf[BUFFER_SIZE];
    int ret = 0;
    int fail = 1;
    sprintf(fn, "/proc/%d/status", pid);
    pf = fopen(fn, "re");
    int m = strlen(mark);
    while (pf && fgets(buf, BUFFER_SIZE - 1, pf)) {

        buf[strlen(buf) - 1] = 0;
        if (strncmp(buf, mark, m) == 0) {
            if(1 == sscanf(buf + m + 1, "%d", &ret))
            {
                fail = 0;
            }
        }
    }
    if (pf)
        fclose(pf);
    if(fail)
        return -1;
    else
        return ret;
}

long get_file_size(const char * filename) {
    struct stat f_stat;

    if (stat(filename, &f_stat) == -1) {
        return 0;
    }

    return (long) f_stat.st_size;
}

void run_solution()
{
    nice(19);

    chdir(work_dir);

    execute_cmd("chmod 775 %s", work_dir);

    execute_cmd("mkdir -p bin usr lib lib64 etc/alternatives proc tmp dev input");
    execute_cmd("mount -o bind -o ro /bin bin >/dev/null 2>/dev/null");
    execute_cmd("mount -o bind -o ro /usr usr >/dev/null 2>/dev/null");
    execute_cmd("mount -o bind -o ro /lib lib >/dev/null 2>/dev/null");
    execute_cmd("mount -o bind -o ro %s input >/dev/null 2>/dev/null", input_dir);
#ifndef __i386
    execute_cmd("mount -o bind -o ro /lib64 lib64 >/dev/null 2>/dev/null");
#endif
    execute_cmd("mount -o bind -o ro /etc/alternatives etc/alternatives >/dev/null 2>/dev/null");
    execute_cmd("mount -o bind -o ro /proc proc >/dev/null 2>/dev/null");
    chroot(work_dir);

    execute_cmd("chmod 775 %s", program_file);

    struct rlimit LIM;

    // CPU time
    LIM.rlim_max = LIM.rlim_cur = time_limit + 1;
    setrlimit(RLIMIT_CPU, &LIM);

    alarm(0);
    alarm(time_limit * 10);

    // file limit
    LIM.rlim_max = STD_F_LIM + STD_MB;
    LIM.rlim_cur = STD_F_LIM;
    setrlimit(RLIMIT_FSIZE, &LIM);

    // proc limit
    LIM.rlim_cur = LIM.rlim_max = 1;
    setrlimit(RLIMIT_NPROC, &LIM);

    // stack limit
    LIM.rlim_cur = LIM.rlim_max = STD_STACK_LIM;
    setrlimit(RLIMIT_STACK, &LIM);

    // set the memory
    LIM.rlim_cur = STD_MB * mem_limit / 2 * 3;
    LIM.rlim_max = STD_MB * mem_limit * 2;
    setrlimit(RLIMIT_AS, &LIM);

    while (setgid(userid) != 0) sleep(1);
    while (setuid(userid) != 0) sleep(1);
    while (setresuid(userid, userid, userid) != 0) sleep(1);

    //open the files
    freopen(standard_input_file, "r", stdin);
    freopen(output_file, "w", stdout);
    freopen(error_file, "w", stderr);

    // trace me
    ptrace(PTRACE_TRACEME, 0, NULL, NULL);

    execl(program_file, program_file, (char *) NULL);

    fflush(stderr);
    exit(0);
}

void watch_solution(pid_t pid_child)
{
    const int call_array_size = 512;
    int call_counter[call_array_size] = { 0 };
    for (int i = 0; i==0||LANG_CV[i]; i++) {
        call_counter[LANG_CV[i]] = 1;
    }

    int result = JUDGE_AC;

    int topmemory = 0; /* top memory usage */
    int tempmemory; /* temp memory usage */

    int status;
    struct user_regs_struct reg; /* register */
    struct rusage ruse;

    if(topmemory==0)
    {
        topmemory = get_proc_status(pid_child, "VmRSS:");
        if(-1 != topmemory)
            topmemory = topmemory << 10;
    }


    while (1) {
        wait4(pid_child, &status, 0, &ruse);

        // check memory
        tempmemory = get_proc_status(pid_child, "VmPeak:");
        if(tempmemory != -1)
        {
            tempmemory = tempmemory << 10;
            if (tempmemory > topmemory)
                topmemory = tempmemory;
            if (topmemory > mem_limit * STD_MB) {
                result = JUDGE_MLE;
                ptrace(PTRACE_KILL, pid_child, NULL, NULL);
                break;
            }
        }

        // check if the program exited
        if (WIFEXITED(status))
            break;

        // check error file
        if (get_file_size(error_file)) {
            result = JUDGE_RE;
            ptrace(PTRACE_KILL, pid_child, NULL, NULL);
            break;
        }

        // check exit code
        int exitcode = WEXITSTATUS(status);
        if (exitcode == 0x05 || exitcode == 0) { } //exitcode == 5 waiting for next CPU allocation
        else {
            if (result == JUDGE_AC) {
                switch (exitcode) {
                case SIGCHLD:
                case SIGALRM:
                    alarm(0);
                case SIGKILL:
                case SIGXCPU:
                    result = JUDGE_TLE;
                    break;
                case SIGXFSZ:
                    result = JUDGE_OLE;
                    break;
                default:
                    result = JUDGE_RE;
                }
            }
            ptrace(PTRACE_KILL, pid_child, NULL, NULL);
            break;
        }

        if (WIFSIGNALED(status)) {
            int sig = WTERMSIG(status);

            if (result == JUDGE_AC) {
                switch (sig) {
                case SIGCHLD:
                case SIGALRM:
                    alarm(0);
                case SIGKILL:
                case SIGXCPU:
                    result = JUDGE_TLE;
                    break;
                case SIGXFSZ:
                    result = JUDGE_OLE;
                    break;
                default:
                    result = JUDGE_RE;
                }
            }
            break;
        }

        // check system calls
        ptrace(PTRACE_GETREGS, pid_child, NULL, &reg);
        if (call_counter[reg.REG_SYSCALL] ){
            //call_counter[reg.REG_SYSCALL]--;
        }else {
            result = JUDGE_RF;
            ptrace(PTRACE_KILL, pid_child, NULL, NULL);
        }

        ptrace(PTRACE_SYSCALL, pid_child, NULL, NULL);
    }

    int usedtime = 0;
    usedtime += (ruse.ru_utime.tv_sec * 1000 + ruse.ru_utime.tv_usec / 1000);
    usedtime += (ruse.ru_stime.tv_sec * 1000 + ruse.ru_stime.tv_usec / 1000);

    printf("%d %d %d\n", result, usedtime, topmemory);

    chdir(work_dir);
    execute_cmd("umount bin usr lib input lib64 etc/alternatives proc 2>/dev/null >/dev/null");
    execute_cmd("umount bin usr lib input lib64 etc/alternatives proc 2>/dev/null >/dev/null");
    execute_cmd("rmdir bin usr lib input lib64 etc/alternatives proc etc tmp dev 2>/dev/null >/dev/null");
}

int main(int argc, char ** argv)
{
    // judge work_dir input output error mem_limit time_limit
    if(argc != 10)
    {
        printf("usage\n\t%s work_dir program_file output_file error_file input_dir standard_input_file time_limit mem_limit userid\n", argv[0]);
        return -1;
    }

    work_dir = argv[1];
    program_file = argv[2];
    output_file = argv[3];
    error_file = argv[4];

    input_dir = argv[5];
    standard_input_file = argv[6];
    time_limit = atoi(argv[7]);
    mem_limit = atoi(argv[8]);

    userid = atoi(argv[9]);

    if(mem_limit>1024) mem_limit = 1024;
    if(mem_limit<0) mem_limit = 0;
    if(time_limit>3600) time_limit=3600;

    pid_t child;
    child = fork();
    if(child == 0)
    { /* child process */
        run_solution();
    }
    else
    {
        watch_solution(child);
    }
}
