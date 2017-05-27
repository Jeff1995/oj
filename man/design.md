# Design Note

Two kind of nodes, manager node and compute node.
Manager node is both the job manager, database server and web server.
Compute node is the job worker (We can actually scale to many compute nodes).

## Web

* Back-end: PHP?

## Job management and security

* Use ubuntu as system
* Use slurm as job management system
* Use cgroup as time, memory control
* Use apparmor as fs access control

## Key processes

### Problem submission

* Web back-end on manager node save description, standard input, standard output and register the submission in database

### Solution submission

* Web back-end on manager node save the source code and register the submission in database
* Web back-end calls a module to test the source code via `slurm`
    - The module is actually located on compute nodes
    - The module check if the standard input/output can be found locally, and `GET` them from manager node if necessary
    - The module `GET` source code from the manager node via web service on the manager node
    - The module test the source code
    - The module `POST` test result back to manager node
* Web back-end receive the `POST` and register test result in the database
* User front-end constantly ask if the job is finished (like every 3 seconds), and get the result once back-end on manager node receives result from compute node

### Solution testing

* Apparmor + cgroups
