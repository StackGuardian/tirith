package stackguardian.ec2.LaunchConfigEBSEncryption

default isPassed = false

isPassed  {
	input_resource_changes := input.resource_changes[k]
	input_resource_changes.type == "aws_instance"
	input_resource_changes_attrs := input_resource_changes.change.after

    # TF will create unencrypted EBS root by default if whole root_block_device block is omitted therefore checking if its exists or not
    root_block_device := input_resource_changes_attrs.root_block_device

    ebs_block_device := input_resource_changes_attrs.ebs_block_device[0].encrypted
    ebs_block_device = true
}


# https://play.openpolicyagent.org/p/u1Rb0NBGPe