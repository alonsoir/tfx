# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for tfx.types.artifact_utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json

# Standard Imports

import tensorflow as tf
from tfx.proto import example_gen_pb2
from tfx.types.channel import Channel
from tfx.types.component_spec import ChannelParameter
from tfx.types.component_spec import ComponentSpec
from tfx.types.component_spec import ExecutionParameter


class _BasicComponentSpec(ComponentSpec):

  PARAMETERS = {
      'folds': ExecutionParameter(type=int),
      'proto': ExecutionParameter(type=example_gen_pb2.Input, optional=True),
  }
  INPUTS = {
      'input': ChannelParameter(type_name='InputType'),
  }
  OUTPUTS = {
      'output': ChannelParameter(type_name='OutputType'),
  }
  _INPUT_COMPATIBILITY_ALIASES = {
      'future_input_name': 'input',
  }
  _OUTPUT_COMPATIBILITY_ALIASES = {
      'future_output_name': 'output',
  }


class ComponentSpecTest(tf.test.TestCase):

  def testComponentspecEmpty(self):

    class EmptyComponentSpec(ComponentSpec):
      PARAMETERS = {}
      INPUTS = {}
      OUTPUTS = {}

    _ = EmptyComponentSpec()

  def testComponentspecBasic(self):
    proto = example_gen_pb2.Input()
    proto.splits.extend([
        example_gen_pb2.Input.Split(name='name1', pattern='pattern1'),
        example_gen_pb2.Input.Split(name='name2', pattern='pattern2'),
        example_gen_pb2.Input.Split(name='name3', pattern='pattern3'),
    ])
    input_channel = Channel(type_name='InputType')
    output_channel = Channel(type_name='OutputType')
    spec = _BasicComponentSpec(
        folds=10, proto=proto, input=input_channel, output=output_channel)
    # Verify proto property.
    self.assertIsInstance(spec.exec_properties['proto'], str)
    decoded_proto = json.loads(spec.exec_properties['proto'])
    self.assertCountEqual(['splits'], decoded_proto.keys())
    self.assertEqual(3, len(decoded_proto['splits']))
    self.assertCountEqual(['name1', 'name2', 'name3'],
                          list(s['name'] for s in decoded_proto['splits']))
    self.assertCountEqual(['pattern1', 'pattern2', 'pattern3'],
                          list(s['pattern'] for s in decoded_proto['splits']))

    # Verify other properties.
    self.assertEqual(10, spec.exec_properties['folds'])
    self.assertIs(spec.inputs['input'], input_channel)
    self.assertIs(spec.outputs['output'], output_channel)

    # Verify compatibility aliasing behavior.
    self.assertIs(spec.inputs['future_input_name'], spec.inputs['input'])
    self.assertIs(spec.outputs['future_output_name'], spec.outputs['output'])

    with self.assertRaisesRegexp(
        TypeError,
        "Expected type <(class|type) 'int'> for parameter u?'folds' but got "
        'string.'):
      spec = _BasicComponentSpec(
          folds='string', input=input_channel, output=output_channel)

    with self.assertRaisesRegexp(
        TypeError,
        '.*should be a Channel of .*InputType.*got (.|\\s)*WrongType.*'):
      spec = _BasicComponentSpec(
          folds=10, input=Channel(type_name='WrongType'), output=output_channel)

    with self.assertRaisesRegexp(
        TypeError,
        '.*should be a Channel of .*OutputType.*got (.|\\s)*WrongType.*'):
      spec = _BasicComponentSpec(
          folds=10, input=input_channel, output=Channel(type_name='WrongType'))

  def testInvalidComponentspecMissingProperties(self):

    with self.assertRaisesRegexp(TypeError, "Can't instantiate abstract class"):

      class InvalidComponentSpecA(ComponentSpec):
        # Missing PARAMETERS.
        INPUTS = {}
        OUTPUTS = {}

      InvalidComponentSpecA()

    with self.assertRaisesRegexp(TypeError, "Can't instantiate abstract class"):

      class InvalidComponentSpecB(ComponentSpec):
        PARAMETERS = {}
        # Missing INPUTS.
        OUTPUTS = {}

      InvalidComponentSpecB()

    with self.assertRaisesRegexp(TypeError, "Can't instantiate abstract class"):

      class InvalidComponentSpecC(ComponentSpec):
        PARAMETERS = {}
        INPUTS = {}
        # Missing OUTPUTS.

      InvalidComponentSpecC()

  def testInvalidComponentspecWrongProperties(self):

    with self.assertRaisesRegexp(TypeError,
                                 'must override PARAMETERS with a dict'):

      class InvalidComponentSpecA(ComponentSpec):
        PARAMETERS = object()
        INPUTS = {}
        OUTPUTS = {}

      InvalidComponentSpecA()

    with self.assertRaisesRegexp(TypeError, 'must override INPUTS with a dict'):

      class InvalidComponentSpecB(ComponentSpec):
        PARAMETERS = {}
        INPUTS = object()
        OUTPUTS = {}

      InvalidComponentSpecB()

    with self.assertRaisesRegexp(TypeError,
                                 'must override OUTPUTS with a dict'):

      class InvalidComponentSpecC(ComponentSpec):
        PARAMETERS = {}
        INPUTS = {}
        OUTPUTS = object()

      InvalidComponentSpecC()

  def testInvalidComponentspecWrongType(self):

    class WrongTypeComponentSpecA(ComponentSpec):
      PARAMETERS = {'x': object()}
      INPUTS = {}
      OUTPUTS = {}

    with self.assertRaisesRegexp(ValueError,
                                 'expects .* dicts are _ComponentParameter'):
      _ = WrongTypeComponentSpecA()

    class WrongTypeComponentSpecB(ComponentSpec):
      PARAMETERS = {'x': ChannelParameter(type_name='X')}
      INPUTS = {}
      OUTPUTS = {}

    with self.assertRaisesRegexp(TypeError,
                                 'expects values of type ExecutionParameter'):
      _ = WrongTypeComponentSpecB()

    class WrongTypeComponentSpecC(ComponentSpec):
      PARAMETERS = {}
      INPUTS = {'x': ExecutionParameter(type=int)}
      OUTPUTS = {}

    with self.assertRaisesRegexp(TypeError,
                                 'expect values of type ChannelParameter'):
      _ = WrongTypeComponentSpecC()

    class WrongTypeComponentSpecD(ComponentSpec):
      PARAMETERS = {}
      INPUTS = {'x': ExecutionParameter(type=int)}
      OUTPUTS = {}

    with self.assertRaisesRegexp(TypeError,
                                 'expect values of type ChannelParameter'):
      _ = WrongTypeComponentSpecD()

  def testInvalidComponentspecDuplicateProperty(self):

    class DuplicatePropertyComponentSpec(ComponentSpec):
      PARAMETERS = {'x': ExecutionParameter(type=int)}
      INPUTS = {'x': ChannelParameter(type_name='X')}
      OUTPUTS = {}

    with self.assertRaisesRegexp(ValueError, 'has a duplicate argument'):
      _ = DuplicatePropertyComponentSpec()

  def testComponentspecMissingArguments(self):

    class SimpleComponentSpec(ComponentSpec):
      PARAMETERS = {
          'x': ExecutionParameter(type=int),
          'y': ExecutionParameter(type=int, optional=True),
      }
      INPUTS = {'z': ChannelParameter(type_name='Z')}
      OUTPUTS = {}

    with self.assertRaisesRegexp(ValueError, 'Missing argument'):
      _ = SimpleComponentSpec(x=10)

    with self.assertRaisesRegexp(ValueError, 'Missing argument'):
      _ = SimpleComponentSpec(z=Channel(type_name='Z'))

    # Okay since y is optional.
    _ = SimpleComponentSpec(x=10, z=Channel(type_name='Z'))


if __name__ == '__main__':
  tf.test.main()
