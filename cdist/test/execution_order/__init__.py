# -*- coding: utf-8 -*-
#
# 2010-2011 Steven Armstrong (steven-cdist at armstrong.cc)
# 2012-2013 Nico Schottelius (nico-cdist at schottelius.org)
#
# This file is part of cdist.
#
# cdist is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cdist is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cdist. If not, see <http://www.gnu.org/licenses/>.
#
#

import os
import shutil

import cdist
from cdist import test
from cdist import core
from cdist import config
from cdist.exec import local
from cdist.core import manifest
import cdist.context


import os.path as op
my_dir = op.abspath(op.dirname(__file__))
fixtures = op.join(my_dir, 'fixtures')
object_base_path = op.join(fixtures, 'object')
type_base_path = op.join(fixtures, 'type')
add_conf_dir = op.join(fixtures, 'conf')


class ResolverTestCase(test.CdistTestCase):

    def setUp(self):
        self.objects = list(core.CdistObject.list_objects(object_base_path, type_base_path))
        self.object_index = dict((o.name, o) for o in self.objects)

    def tearDown(self):
        for o in self.objects:
            o.requirements = []

    def test_find_requirements_by_name_string(self):
        requirements = ['__first/man', '__second/on-the', '__third/moon']
        required_objects = [self.object_index[name] for name in requirements]
        # self.assertEqual(sorted(list(self.dependency_resolver.find_requirements_by_name(requirements))),
        #     sorted(required_objects))
        self.assertTrue(False)

    def test_find_requirements_by_name_pattern(self):
        requirements = ['__first/*', '__second/*-the', '__third/moon']
        requirements_expanded = [
            '__first/child', '__first/dog', '__first/man', '__first/woman',
            '__second/on-the', '__second/under-the',
            '__third/moon'
        ]
        required_objects = [self.object_index[name] for name in requirements_expanded]
        self.assertEqual(sorted(list(self.dependency_resolver.find_requirements_by_name(requirements))),
            sorted(required_objects))
        self.assertTrue(False)

    def test_dependency_resolution(self):
        first_man = self.object_index['__first/man']
        second_on_the = self.object_index['__second/on-the']
        third_moon = self.object_index['__third/moon']
        first_man.requirements = [second_on_the.name]
        second_on_the.requirements = [third_moon.name]
        self.assertEqual(
            self.dependency_resolver.dependencies['__first/man'],
            [third_moon, second_on_the, first_man]
        )
        self.assertTrue(False)

    def test_circular_reference(self):
        first_man = self.object_index['__first/man']
        first_woman = self.object_index['__first/woman']
        first_man.requirements = [first_woman.name]
        first_woman.requirements = [first_man.name]
        with self.assertRaises(resolver.CircularReferenceError):
            self.dependency_resolver.dependencies
        self.assertTrue(False)

    def test_requirement_not_found(self):
        first_man = self.object_index['__first/man']
        first_man.requirements = ['__does/not/exist']
        with self.assertRaises(cdist.Error):
            self.dependency_resolver.dependencies
        self.assertTrue(False)

class AutorequireTestCase(test.CdistTestCase):

    def setUp(self):
        self.orig_environ = os.environ
        os.environ = os.environ.copy()
        self.temp_dir = self.mkdtemp()

        self.out_dir = os.path.join(self.temp_dir, "out")
        self.remote_out_dir = os.path.join(self.temp_dir, "remote")

        os.environ['__cdist_out_dir'] = self.out_dir
        os.environ['__cdist_remote_out_dir'] = self.remote_out_dir

        self.context = cdist.context.Context(
            target_host=self.target_host,
            remote_copy=self.remote_copy,
            remote_exec=self.remote_exec,
            add_conf_dirs=[add_conf_dir],
            exec_path=test.cdist_exec_path,
            debug=False)

        self.config = config.Config(self.context)

    def tearDown(self):
        os.environ = self.orig_environ
        shutil.rmtree(self.temp_dir)

    def test_implicit_dependencies(self):
        self.context.initial_manifest = os.path.join(self.context.local.manifest_path, 'implicit_dependencies')
        self.config.stage_prepare()

        objects = core.CdistObject.list_objects(self.context.local.object_path, self.context.local.type_path)
        dependency_resolver = resolver.DependencyResolver(objects)
        expected_dependencies = [
            dependency_resolver.objects['__package_special/b'],
            dependency_resolver.objects['__package/b'],
            dependency_resolver.objects['__package_special/a']
        ]
        resolved_dependencies = dependency_resolver.dependencies['__package_special/a']
        self.assertEqual(resolved_dependencies, expected_dependencies)
        self.assertTrue(False)

    def test_circular_dependency(self):
        self.context.initial_manifest = os.path.join(self.context.local.manifest_path, 'circular_dependency')
        self.config.stage_prepare()
        # raises CircularDependecyError
        self.config.stage_run()
        self.assertTrue(False)

    def test_recursive_type(self):
        self.context.initial_manifest = os.path.join(self.config.local.manifest_path, 'recursive_type')
        self.config.stage_prepare()
        # raises CircularDependecyError
        self.config.stage_run()
        self.assertTrue(False)
