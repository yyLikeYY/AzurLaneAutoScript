import os
import re

from deploy.logger import logger


def patch_trust_env(file):
    """
    People use proxies, but they never realize that proxy software leaves a
    global proxy pointing to itself even when the software is not running.
    In most situations we set `session.trust_env = False` in requests, but this
    does not effect the `pip` command.

    To handle untrusted user environment for good. We patch the code file in
    requests directly. Of course, the patch only effect the python env inside
    Alas.

    Returns:
        bool: If patched.
    """
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        if re.search('self.trust_env = True', content):
            content = re.sub('self.trust_env = True', 'self.trust_env = False', content)
            with open(file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f'{file} trust_env patched')
        elif re.search('self.trust_env = False', content):
            logger.info(f'{file} trust_env already patched')
        else:
            logger.info(f'{file} trust_env not found')
    else:
        logger.info(f'{file} trust_env no need to patch')


def check_running_directory():
    """
    An fool-proof mechanism.
    Show error if user is running Easy Install in compressing software,
    since Alas can't install in temp directories.
    """
    file = __file__.replace(r"\\", "/").replace("\\", "/")
    # C:/Users/<user>/AppData/Local/Temp/360zip$temp/360$3/AzurLaneAutoScript
    if 'Temp/360zip' in file:
        logger.critical('请先解压Alas的压缩包，再安装Alas')
        exit(1)
    # C:/Users/<user>/AppData/Local/Temp/Rar$EXa9248.23428/AzurLaneAutoScript
    if 'Temp/Rar' in file or 'Local/Temp' in file:
        logger.critical('Please unzip ALAS installer first')
        exit(1)


def patch_uiautomator2():
    """
    uiautomator2 download assets from https://tool.appetizer.io first then fallback to https://github.com/openatx.
    https://tool.appetizer.io is added to bypass the wall in China but https://tool.appetizer.io is slow outside of CN
    plus some CN users cannot access it for unknown reason.

    So we patch `uiautomator2/init.py` to a local assets cache `uiautomator2cache/cache`.
        appdir = os.path.join(os.path.expanduser('~'), '.uiautomator2')
    to:
        appdir = os.path.abspath(os.path.join(__file__, '../../uiautomator2cache'))

    And we also remove minicap installations since emulators doesn't need it.
        for url in self.minicap_urls:
            self.push_url(url)
    to:
        for url in []:
            self.push_url(url)
    """
    cache_dir = './toolkit/Lib/site-packages/uiautomator2cache/cache'
    init_file = './toolkit/Lib/site-packages/uiautomator2/init.py'
    appdir = "os.path.abspath(os.path.join(__file__, '../../uiautomator2cache'))"

    if not os.path.exists(init_file):
        logger.info('uiautomator2 is not installed skip patching')
        return

    modified = False
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Patch minicap_urls
    res = re.search(r'self.minicap_urls', content)
    if res:
        content = re.sub(r'self.minicap_urls', '[]', content)
        modified = True
        logger.info(f'{init_file} minicap_urls patched')
    else:
        logger.info(f'{init_file} minicap_urls no need to patch')

    # Patch appdir
    if os.path.exists(cache_dir):
        res = re.search(r'appdir ?=(.*)\n', content)
        if res:
            prev = res.group(1).strip()
            if prev == appdir:
                logger.info(f'{init_file} appdir already patched')
            else:
                content = re.sub(r'appdir ?=.*\n', f'appdir = {appdir}\n', content)
                modified = True
                logger.info(f'{init_file} appdir patched')
        else:
            logger.info(f'{init_file} appdir not found')
    else:
        logger.info('uiautomator2cache is not installed skip patching')

    # Save file
    if modified:
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f'{init_file} content saved')


def pre_checks():
    check_running_directory()

    # patch_trust_env
    patch_trust_env('./toolkit/Lib/site-packages/requests/sessions.py')
    patch_trust_env('./toolkit/Lib/site-packages/pip/_vendor/requests/sessions.py')

    patch_uiautomator2()


if __name__ == '__main__':
    pre_checks()
