#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012, 2015-2016 IOPixel SAS
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

__version__ = '1.1.0'

import sys
import argparse
import subprocess
import json
import os
import shutil
import logging
import platform
import re
import tempfile
import signal

DESCRIPTION = """
Create Private Ethereum Blockchain
 by ellis2323 & regispietra
 https://github.com/regispietra/CreatePrivateEthereum

This script pilots geth to provide easy functions:

* ./pgeth.py init
   this function create the blockchain with an account

* ./pgeth.py start
   this function starts geth daemon and mining. When it has started, you could use your Ethereun Wallet to see
   contracts and tokens.

* ./pgeth.py stop
    this functions stops geth

* ./pgeth.py destroy
   A function to delete quickly your private blockchain.

"""

logger = logging.getLogger('pgeth')


# const in python
PIDFILE = os.path.join(tempfile.gettempdir(), "geth.pid")
CONFIG_FILE = "pgeth_config.json"
DEFAULT_CONFIG = {
  "datadir": os.path.join(os.path.expanduser("~"), "private_ethereum_blockchain"),
  "password": "apasswordtochange"
}

GENESIS = {
 "config": {
     "chainId": 15
  },
  "nonce": "0xdeadbeefdeadbeef",
  "timestamp": "0x0",
  "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
  "extraData": "0x00",
  "gasLimit": "0x8000000",
  "difficulty": "0x400",
  "mixhash": "0x0000000000000000000000000000000000000000000000000000000000000000",
  "coinbase": "0x0000000000000000000000000000000000000000",
  "alloc": {
  }
}


def load_config_key(key):
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as cfg:
                data = json.load(cfg)
        except OSError:
            logger.exception("Error reading config file")
        else:
            return data.get(key)
    logger.error("No config file exists, creating default config")
    with open(CONFIG_FILE, 'w') as cfg:
        json.dump(DEFAULT_CONFIG, cfg, indent=2)
    return DEFAULT_CONFIG.get(key)


def get_data_dir():
    """Load datadir key and expand it"""
    return os.path.expanduser(load_config_key("datadir"))


def get_ipc_dir():
    """Create default ipc path"""
    pl = platform.system()
    ipc_dirs = {
        "Darwin": "~/Library/Ethereum/geth.ipc",
        "Windows": "~\\AppData\\Roaming\\Ethereum\\geth.ipc",
        "Linux": "~/.ethereum/geth.ipc"
    }
    if pl not in ipc_dirs:
        logger.error('Platform unknown "%s". Contact devs at iopixel.com', platform)
        return sys.exit(-1)

    ipcdir = os.path.expanduser(ipc_dirs[pl])
    return ipcdir


def directory_exists(path):
    """Check the path exists and it is a directory"""
    if not os.path.exists(path):
        return False
    if not os.path.isdir(path):
        return False
    return True


def file_exists(path):
    """Check the path exists and it is a file"""
    if not os.path.exists(path):
        return False
    if not os.path.isfile(path) and os.access(path, os.X_OK):
        return False
    return True


def check_geth_command():
    """Search for the geth executable"""
    geth = load_config_key("geth")
    if geth:
        if file_exists(geth):
            return geth
        logger.error("invalid geth path in config file")
        return sys.exit(-1)
    standard_paths = ["/usr/bin/geth", "/usr/local/bin/geth", "/opt/local/bin/geth"]
    if platform.system() == 'Windows':
        standard_paths = ["C:\Program Files\Geth\geth.exe"]
    for p in standard_paths:
        if file_exists(p):
            return p
    logger.error("no geth found in classic path. Use the geth param in the config file")
    sys.exit(0)


def log_command(cmd, level=logging.DEBUG):
    """cmd ie list of word into a string"""
    return logger.log(level, " ".join(cmd))


def test(args):
    return get_address()


def destroy_private_blockchain():
    """Destroy your private blockchain"""
    data_dir = get_data_dir()
    if not directory_exists(data_dir):
        logger.error("nothing to destroy. There is no {} directory".format(data_dir))
        return sys.exit(-1)

    folders = ['chaindata', 'keystore', 'dapp', 'geth', '.DS_Store']
    files = ['nodekey', 'geth.ipc', 'genesis.json', 'mypassword.txt']

    for folder in folders:
        shutil.rmtree(os.path.join(data_dir, folder), ignore_errors=True)

    for file_path in files:
        try:
            os.remove(os.path.join(data_dir, file_path))
        except OSError:
            pass

    try:
        os.rmdir(data_dir)
    except OSError:
        logger.error("We did not destroy {} directory because there is "
                     "something not standard in it.\n"
                     "\tRemove the directory manually "
                     "after checking it's contents".format(data_dir))
        return sys.exit(-1)


def get_address():
    """Get the address of the account 0"""
    datadir = get_data_dir()
    geth = check_geth_command()
    options = ["--datadir", datadir]
    list_accounts_cmd = [geth] + options + ["account", "list"]
    logger.debug("cmd: " + " ".join(list_accounts_cmd))
    res = subprocess.check_output(list_accounts_cmd).decode('utf-8')
    num_accounts = len(res.split('\n')) - 1
    if not num_accounts:
        return None
    line = res.split('\n')[0]
    regexp = re.search(u"{([0-9abcdefABCDEF]+)}", line)
    if regexp is None:
        logger.error("No address found in keystore")
        return sys.exit(-1)
    result = regexp.group(1)
    logger.debug('adress found: 0x' + result)
    return result


def init_account():
    """List accounts. Create a default one if there is none"""
    data_dir = get_data_dir()
    geth = check_geth_command()
    options = ["--datadir", data_dir]
    list_accounts_cmd = [geth] + options + ["account", "list"]
    log_command(list_accounts_cmd)
    res = subprocess.check_output(list_accounts_cmd).decode('utf-8')
    num_accounts = len(res.split('\n')) - 1

    if num_accounts > 0:
        return

    with open(os.path.join(data_dir, "mypassword.txt"), "w") as pass_file:
        pass_file.write(load_config_key("password"))
    # create an account
    create_account_cmd = [geth] + options + ["--password", os.path.join(data_dir, "mypassword.txt"), "account", "new"]
    log_command(create_account_cmd)
    subprocess.call(create_account_cmd)


def is_geth_running():
    """Check if there is a geth running"""
    return file_exists(PIDFILE)


def init(args):
    """init command"""
    # account management
    init_account()

    # init needed if there is no chaindata dir
    data_dir = get_data_dir()
    if (directory_exists(os.path.join(data_dir, 'chaindata')) or
            directory_exists(os.path.join(data_dir, 'geth', 'chaindata'))):
        return
    geth = check_geth_command()

    # create the json genesis
    address = get_address()
    GENESIS['alloc']["0x{}".format(address)] = {"balance": "1000000000000000000000"}
    genesis_file = os.path.join(data_dir, "genesis.json")
    with open(genesis_file, "w") as gen:
        json.dump(GENESIS, gen, indent=2)

    # launch the blockchain with the CustomGenesis json file
    init_cmd = [geth, "--datadir", data_dir, "--networkid", "100", "init", genesis_file]
    log_command(init_cmd)
    subprocess.call(init_cmd)


def start(args):
    """start the geth daemon"""
    # check if there is a PID File
    if is_geth_running():
        logger.error("geth must already be running (If not remove the %s file)" % PIDFILE)
        sys.exit(1)
    # start geth with mining
    data_dir = load_config_key("datadir")
    geth = check_geth_command()
    options = ["--datadir", data_dir, "--networkid", "100", "--nodiscover", "--nat", "none", "--mine", "--minerthreads",
               "1", "--ipcpath", get_ipc_dir()]
    options += ["--rpc", "--rpcport", "8545", "--rpcapi", "'web3,eth,debug,net,shh'", "--rpccorsdomain", "'*'"]
    start_cmd = [geth] + options
    log_command(start_cmd)
    logfile = open("geth.logs", "w")
    process = subprocess.Popen(start_cmd, stdout=logfile, stderr=logfile)
    # write the the pid file
    with open(PIDFILE, "w") as pid_file:
        pid_file.write(str(process.pid))
    logger.info("geth starting")


def stop(args):
    """stop the geth daemon"""
    # check if there is a PID File
    if not is_geth_running():
        logger.warning("geth is not running")
        return
    # read the pid file
    with open(PIDFILE, "r") as pidfile:
        pid = int(pidfile.read().strip())
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as err:
        pass
    finally:
        logger.info("geth is shutting down")
        os.remove(PIDFILE)


def destroy(args):
    """destroy your private blockchain"""
    destroy_private_blockchain()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S')

    parser = argparse.ArgumentParser(usage=DESCRIPTION)

    subparsers = parser.add_subparsers()

    init_parser = subparsers.add_parser('init')
    init_parser.set_defaults(func=init)

    start_parser = subparsers.add_parser('start')
    start_parser.set_defaults(func=start)

    stop_parser = subparsers.add_parser('stop')
    stop_parser.set_defaults(func=stop)

    destroy_parser = subparsers.add_parser('destroy')
    destroy_parser.set_defaults(func=destroy)

    test_parser = subparsers.add_parser('test')
    test_parser.set_defaults(func=test)

    args = parser.parse_args()
    if not vars(args):
        parser.print_usage()
    else:
        args.func(args)

