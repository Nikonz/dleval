import json
import os
import shutil

def make_dir(path):
    os.makedirs(path, exist_ok=True)

def remove_dir(path):
    shutil.rmtree(path, ignore_errors=True) # FIXME ignore only certain errors

def copy_file(fpath, dest_dir, logger=None):
    if os.path.isfile(fpath):
        shutil.copy(fpath, dest_dir)
    elif logger is not None:
        logger.warning("non-regular file `%s', skip" % fpath)

def copy_all_files(source_dir, dest_dir, logger=None):
    source_files = os.listdir(source_dir)
    for f in source_files:
        fpath = os.path.join(source_dir, f)
        copy_file(fpath, dest_dir, logger)

def parse_json(data, logger=None):
    try:
        return json.loads(data)
    except Exception as e:
        errmsg = e.message if hasattr(e, 'message') else str(e)
        if logger is not None:
            logger.error('can not parse json: ' +
                    errmsg + ' [data=%s]' % data)
        return None
