import json
import os
import shutil

def parse_json(data, logger=None):
    try:
        return (json.loads(data), True)
    except Exception as e:
        errmsg = e.message if hasattr(e, 'message') else str(e)
        if logger is not None:
            logger.error('can not parse json: ' +
                    errmsg + ' [data=%s]' % data)
        return (None, False)

def pack_json(data):
    return json.dumps(data)

def copy_file(fpath, dest_dir, logger=None):
    if os.path.isfile(fpath):
        shutil.copy(fpath, dest_dir)
    elif logger is not None:
        logger.warning("non-regular file `%s', skip" % fpath)

def copy_all_files(source_dir, dest_dir, logger=None):
    source_files = os.listdir(source_dir)
    for f in source_files:
        # FIXME use os.path.join everywhere
        fpath = os.path.join(source_dir, f)
        copy_file(fpath, dest_dir, logger)

def get_submission_directory(assignment_id, user_id, attempt):
    return ('./data/assignment_%d/user_%d/attempt_%d' % \
            (assignment_id, user_id, attempt))

def get_evaluator_directory(assignment_id):
    return ('./data/assignment_%d/evaluator' % assignment_id)

def get_assignments_info_directory():
    return './data'

def get_docker_directory():
    return './docker'
