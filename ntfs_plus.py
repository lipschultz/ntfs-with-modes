import json
import sys
from collections import defaultdict

from fuse import FUSE

sys.path.insert(0, '.')

from passthrough import Passthrough


class NTFSPlus(Passthrough):
    def __init__(self, root, permissions_json, debug=True):
        super().__init__(root, debug=debug)
        self.permissions = defaultdict(lambda: defaultdict())  # {full_path -> {setting -> values, ...}, ...}
        with open(permissions_json) as fp:
            stored_permissions = json.load(fp)
        self.permissions.update(stored_permissions)

    def update_permissions(self, path, setting, value):
        self.permissions[path][setting] = value

    def chmod(self, path, mode):
        print(f'chmod {mode} {path}')
        full_path = self._full_path(path)
        self.update_permissions(path, 'mode', mode)
        print(f'\t{self.permissions}')

    def chown(self, path, uid, gid):
        print(f'chown {uid}:{gid} {path}')
        full_path = self._full_path(path)
        if uid != -1:
            self.permissions[full_path]['owner-user'] = uid
        if gid != -1:
            self.permissions[full_path]['owner-group'] = gid
        print(f'\t{self.permissions}')

    def getattr(self, path, fh=None):
        # self.print('getattr:', path)
        retval = super().getattr(path, fh)
        full_path = self._full_path(path)

        permissions = self.permissions.get(full_path)
        if permissions is not None:
            if 'mode' in permissions:
                retval['st_mode'] = permissions['mode']
            if 'owner-user' in permissions:
                retval['st_uid'] = permissions['owner-user']
            if 'owner-group' in permissions:
                retval['st_gid'] = permissions['owner-group']

        return retval

    # def statfs(self, path):
    #     if self.is_generated_directory(path):
    #         return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)
    #     else:
    #         return super().statfs(path)


def main(mountpoint, root, foreground=True):
    FUSE(NTFSPlus(root), mountpoint, nothreads=True, foreground=foreground)  # , allow_other=True)


if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])