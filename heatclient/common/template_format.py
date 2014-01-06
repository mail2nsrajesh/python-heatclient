# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
import yaml

HEAT_VERSIONS = (u'2012-12-12',)
CFN_VERSIONS = (u'2010-09-09',)

if hasattr(yaml, 'CSafeLoader'):
    yaml_loader = yaml.CSafeLoader
else:
    yaml_loader = yaml.SafeLoader

if hasattr(yaml, 'CSafeDumper'):
    yaml_dumper = yaml.CSafeDumper
else:
    yaml_dumper = yaml.SafeDumper


def _construct_yaml_str(self, node):
    # Override the default string handling function
    # to always return unicode objects
    return self.construct_scalar(node)
yaml_loader.add_constructor(u'tag:yaml.org,2002:str', _construct_yaml_str)
# Unquoted dates like 2013-05-23 in yaml files get loaded as objects of type
# datetime.data which causes problems in API layer when being processed by
# openstack.common.jsonutils. Therefore, make unicode string out of timestamps
# until jsonutils can handle dates.
yaml_loader.add_constructor(u'tag:yaml.org,2002:timestamp',
                            _construct_yaml_str)


def parse(tmpl_str):
    '''Takes a string and returns a dict containing the parsed structure.

    This includes determination of whether the string is using the
    JSON or YAML format.
    '''
    if tmpl_str.startswith('{'):
        tpl = json.loads(tmpl_str)
    else:
        try:
            tpl = yaml.load(tmpl_str, Loader=yaml_loader)
        except yaml.YAMLError as yea:
            raise ValueError(yea)
        else:
            if tpl is None:
                tpl = {}
            if u'heat_template_version' not in tpl:
                default_for_missing(tpl, u'HeatTemplateFormatVersion',
                                    HEAT_VERSIONS)
    return tpl


def default_for_missing(tpl, version_param, versions):
    '''Checks a parsed template for missing version and sections.

    This is currently only applied to YAML templates.
    '''
    # if version is missing, implicitly use the lastest one
    if version_param not in tpl:
        tpl[version_param] = versions[-1]

    # create empty placeholders for any of the main dict sections
    for param in (u'Parameters', u'Mappings', u'Resources', u'Outputs'):
        if param not in tpl:
            tpl[param] = {}
