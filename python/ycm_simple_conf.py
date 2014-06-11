import os
import sys
import logging
import xml.etree.ElementTree as et
import re
import subprocess


class SimpleConf(object):

    def __init__(self, file_name):
        self.m_compiled_file = file_name
        self.m_root_dir = None
        self.m_config_file = None
        self.m_project_type = 'c++'
        self.m_user_include_path = list()
        self.m_default_include_path = list()
        self.seek_config_file(os.path.dirname(self.m_compiled_file))
        self.parse_config_file()
        self.fetch_default_include_path()

    @property
    def compiled_file(self):
        return self.m_compiled_file

    @property
    def root_dir(self):
        return self.m_root_dir

    @property
    def config_file(self):
        return self.m_config_file

    @property
    def project_type(self):
        return self.m_project_type

    @property
    def user_include_path(self):
        return self.m_user_include_path

    @property
    def default_include_path(self):
        return self.m_default_include_path

    @property
    def flags(self):
        flags = ['-Wall']
        if self.m_project_type == 'c':
            flags.extend(['-std=c99', '-x', 'c'])
        else:
            flags.extend(['-std=c++11', '-x', 'c++'])
        for include in self.m_default_include_path:
            flags.extend(['-isystem', include])
        for include in self.m_user_include_path:
            flags.extend(['-I', include])
        return flags

    def seek_config_file(self, dir_name):
        if dir_name == '' or dir_name == '/':
            logging.warning('Config file not found')
            return
        files = [os.path.join(dir_name, f) for f in os.listdir(dir_name)]
        files = [f for f in files if os.path.isfile(f)]
        for f in files:
            if os.path.basename(f) == '.ycm_simple_conf.xml':
                self.m_root_dir = dir_name
                self.m_config_file = os.path.join(dir_name, f)
                logging.info('Config file found: %s' % self.m_config_file)
                return
        self.seek_config_file(os.path.dirname(dir_name))

    def parse_config_file(self):
        if not self.m_config_file:
            return
        try:
            project = et.parse(self.m_config_file).getroot()
            if project.tag != 'project':
                raise Exception
            self.m_project_type = project.attrib['type']
            if not self.m_project_type in ['c', 'c++']:
                raise Exception
            for include in project.iter('include'):
                inc = os.path.join(self.m_root_dir, include.attrib['path'])
                inc = str.strip(inc)
                self.m_user_include_path.append(inc)
                logging.info('Adding to user include path: %s' % inc)
        except Exception as e:
            logging.error('Failed to parse config file')

    def fetch_default_include_path(self):
        try:
            devnull = open('/dev/null', 'r')
            err = subprocess.check_output(
                    ['cpp', '-x', self.m_project_type, '-v'],
                    stdin = devnull,
                    stderr = subprocess.STDOUT
                 )
            include = []
            pattern = re.compile(
                '#include \<\.{3}\>.*\:(.+)End of search list\.',
                re.DOTALL
                )
            match = pattern.search(err)
            if match:
                lines = str.splitlines(match.group(1))
                for inc in [str.strip(l) for l in lines if l]:
                    logging.info('Adding to default include path: %s' % inc)
                    self.m_default_include_path.append(inc)
        except Exception as e:
            logging.error('Failed to run: cpp -x %s -v' % self.m_project_type)


def FlagsForFile(file_name, **kwargs):
    simple_conf = SimpleConf(file_name)
    flags = simple_conf.flags
    logging.info('Flags used by clang: %s' % flags)
    return {
            'flags': flags,
            'do_cache': True
            }