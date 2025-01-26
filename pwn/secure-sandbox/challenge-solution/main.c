#include <err.h>
#include <unistd.h>
#include <sys/wait.h>
#include <stdlib.h>
#include <stdio.h>
#include <seccomp.h>
#include <sys/mman.h>
#include <limits.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <string.h>
#include <sys/types.h>

typedef void (*void_fn)(void);

void title()
{
  puts("      ______   ________   ______   __    __  _______   ________       ");
  puts("     /      \\ /        | /      \\ /  |  /  |/       \\ /        |      ");
  puts("    /######  |########/ /######  |## |  ## |#######  |########/       ");
  puts("    ## \\__##/ ## |__    ## |  ##/ ## |  ## |## |__## |## |__          ");
  puts("    ##      \\ ##    |   ## |      ## |  ## |##    ##< ##    |         ");
  puts("     ######  |#####/    ## |   __ ## |  ## |#######  |#####/          ");
  puts("    /  \\__## |## |_____ ## \\__/  |## \\__## |## |  ## |## |_____       ");
  puts("    ##    ##/ ##       |##    ##/ ##    ##/ ## |  ## |##       |      ");
  puts("     ######/  ########/  ######/   ######/  ##/   ##/ ########/       ");
  puts("                                                                      ");
  puts(" ______    ______   __    __  _______   _______    ______   __    __  ");
  puts(" /      \\  /      \\ /  \\  /  |/       \\ /       \\  /      \\ /  |  /  |");
  puts("/######  |/######  |##  \\ ## |#######  |#######  |/######  |## |  ## |");
  puts("## \\__##/ ## |__## |###  \\## |## |  ## |## |__## |## |  ## |##  \\/##/ ");
  puts("##      \\ ##    ## |####  ## |## |  ## |##    ##< ## |  ## | ##  ##<  ");
  puts(" ######  |######## |## ## ## |## |  ## |#######  |## |  ## |  ####  \\ ");
  puts("/  \\__## |## |  ## |## |#### |## |__## |## |__## |## \\__## | ## /##  |");
  puts("##    ##/ ## |  ## |## | ### |##    ##/ ##    ##/ ##    ##/ ## |  ## |");
  puts(" ######/  ##/   ##/ ##/   ##/ #######/  #######/   ######/  ##/   ##/ ");
  puts("");
  puts("Your premium choice for truly secure shellcode execution. ");
  puts("Try it for yourself, if you still have doubts.");
  puts("");
}

void setup_seccomp()
{
  scmp_filter_ctx ctx;
  ctx = seccomp_init(SCMP_ACT_KILL);
  int ret = 0;
  ret |= seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 0);
  ret |= seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(open), 0);
  ret |= seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(close), 0);
  ret |= seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(writev), 0);
  ret |= seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(lseek), 0);
  ret |= seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit), 0);
  ret |= seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit_group), 0);
  ret |= seccomp_load(ctx);
  if (ret)
  {
    exit(1);
  }
}

void setup_sandbox(void *shellcode, int shellcode_length)
{
  pid_t pid = fork();
  if (pid > 0)
  {
    printf("[+] hypervisor: started sandbox with pid: %d\n", pid);
    printf("[*] hypervisor: waiting for sandbox to terminate...\n");

    int status;
    waitpid(pid, &status, 0);

    printf("[+] hypervisor: sandbox finished with status code: %d\n", WEXITSTATUS(status));
    return;
  }
  else
  {
    printf("[+] sandbox: executing shellcode with length: %d...\n", shellcode_length);

    void *shellcode_page = mmap(0x0, shellcode_length, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);

    if (shellcode_page == MAP_FAILED)
    {
      puts("mmap failed.");
      exit(1);
    }

    printf("[+] sandbox: shellcode page: %p\n", shellcode_page);

    memcpy(shellcode_page, shellcode, shellcode_length);

    setup_seccomp();

    ((void_fn)shellcode_page)();

    exit(0);
  }
}

int main()
{
  setvbuf(stdin, NULL, _IONBF, 0);
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);
  title();

  printf("\n[+] started hypervisor with pid: %d\n\n", getpid());

  puts("Your shellcode:");

  char s[4096];
  int shellcode_length = read(0, &s, 4096);
  setup_sandbox(&s, shellcode_length);
  puts("thank you for trusting our product.");
}
