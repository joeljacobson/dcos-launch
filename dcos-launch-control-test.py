""" Integration testing for dcos-launch.platforms functions used by dcos-launch-control (tagging and listing
deployments)
"""
import argparse
import json

from dcos_launch import util
from dcos_launch.platforms import gce, aws, arm


def gce_test(deployment_name):
    credentials_path = util.set_from_env('GOOGLE_APPLICATION_CREDENTIALS')
    credentials = util.read_file(credentials_path)
    gce_wrapper = gce.GceWrapper(json.loads(credentials), credentials_path)

    deployment = None
    found = False
    for d in gce_wrapper.get_deployments():
        if d.name == deployment_name:
            found = True
            deployment = d
            break
    assert found

    tags = {'integration test': 'test tagging'}
    deployment.update_tags(tags)
    deployment.wait_for_completion()
    assert deployment.get_tags() == tags


def aws_test(deployment_name):
    boto_wrapper = aws.BotoWrapper(None, util.set_from_env('AWS_ACCESS_KEY_ID'),
                                        util.set_from_env('AWS_SECRET_ACCESS_KEY'))

    stack = None
    found = False
    for s in boto_wrapper.get_all_stacks():
        if s.name == deployment_name:
            found = True
            stack = s
            break
    assert found

    found = False
    for keypair in boto_wrapper.get_all_keypairs():
        if keypair.key_name == deployment_name:
            found = True
            break
    assert found

    stack = aws.CfStack(deployment_name, boto_wrapper)
    tags = {'integration test': 'test tagging'}
    stack.update_tags(tags)
    stack.wait_for_complete()
    assert tags == {entry['Key']: entry['Value'] for entry in stack.stack.tags}


def azure_test(deployment_name):
    azure_wrapper = arm.AzureWrapper(None, util.set_from_env('AZURE_SUBSCRIPTION_ID'),
                                           util.set_from_env('AZURE_CLIENT_ID'),
                                           util.set_from_env('AZURE_CLIENT_SECRET'),
                                           util.set_from_env('AZURE_TENANT_ID'))

    resource_group = None
    found = False
    for rg in azure_wrapper.rmc.resource_groups.list():
        if rg.name == deployment_name:
            resource_group = rg
            found = True
            break
    assert found

    tags = {'integration test': 'test tagging'}
    if resource_group.tags is None:
        resource_group.tags = dict()
    resource_group.tags.update(tags)
    azure_wrapper.rmc.resource_groups.patch(resource_group.name, {
        'tags': resource_group.tags,
        'location': resource_group.location}, raw=True)
    arm.DcosAzureResourceGroup(deployment_name, azure_wrapper).wait_for_deployment()
    #check cluster is in list
    #tag deployment
    #wait for complete
    # get tags and check they're the same as what we tagged


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='test dcos-launch.platforms functions used by dcos-launch-control')
    parser.add_argument(
        '--platform',
        required=True,
        action='store',
        help='What platform to test on? possible values are: {gce, azure, aws}')
    parser.add_argument(
        '--name',
        required=True,
        action='store',
        help='Name of the deployment to test')

    args = parser.parse_args()

    if args.platform == 'gce':
        gce_test(args.name)
    elif args.platform == 'aws':
        aws_test(args.name)
    elif args.platform == 'azure':
        azure_test(args.name)
