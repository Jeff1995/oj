
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
#include "okcalls.h"

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

#define JUDGE_USER_ID 3333 /* user id */

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

#define JUDGE_AC 0
#define JUDGE_RE 1
#define JUDGE_TLE 2
#define JUDGE_MLE 3
#define JUDGE_OLE 4
#define JUDGE_RF 5

#define BUFFER_SIZE 5120

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

    //while (setgid(JUDGE_USER_ID) != 0) sleep(1);
    //while (setuid(JUDGE_USER_ID) != 0) sleep(1);
    //while (setresuid(JUDGE_USER_ID, JUDGE_USER_ID, JUDGE_USER_ID) != 0) sleep(1);

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

    // open the files
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
}

int main(int argc, char ** argv)
{
    // judge work_dir input output error mem_limit time_limit
    if(argc != 8)
    {
        printf("usage\n\t%s work_dir input output error mem_limit time_limit program_file\n", argv[0]);
        return -1;
    }

    work_dir = argv[1];
    standard_input_file = argv[2];
    output_file = argv[3];
    error_file = argv[4];
    mem_limit = atoi(argv[5]);
    time_limit = atoi(argv[6]);
    program_file = argv[7];

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