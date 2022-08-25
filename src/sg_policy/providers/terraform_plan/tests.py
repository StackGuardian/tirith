from . import handler
import json
import pytest


plan_string = """
{
    "format_version": "0.1",
    "terraform_version": "0.14.11",
    "variables": {
        "amazon_side_asn": {
            "value": "64512"
        },
        "assign_ipv6_address_on_creation": {
            "value": false
        },
        "azs": {
            "value": []
        },
        "cidr": {
            "value": "10.0.0.0/18"
        },
        "create_database_internet_gateway_route": {
            "value": false
        },
        "create_database_nat_gateway_route": {
            "value": false
        },
        "create_database_subnet_group": {
            "value": true
        },
        "create_database_subnet_route_table": {
            "value": false
        },
        "create_egress_only_igw": {
            "value": true
        },
        "create_elasticache_subnet_group": {
            "value": true
        },
        "create_elasticache_subnet_route_table": {
            "value": false
        },
        "create_flow_log_cloudwatch_iam_role": {
            "value": false
        },
        "create_flow_log_cloudwatch_log_group": {
            "value": false
        },
        "create_igw": {
            "value": true
        },
        "create_redshift_subnet_group": {
            "value": true
        },
        "create_redshift_subnet_route_table": {
            "value": false
        },
        "create_vpc": {
            "value": true
        },
        "customer_gateway_tags": {
            "value": {}
        },
        "customer_gateways": {
            "value": {}
        },
        "database_acl_tags": {
            "value": {}
        },
        "database_dedicated_network_acl": {
            "value": false
        },
        "database_inbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "database_outbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "database_route_table_tags": {
            "value": {}
        },
        "database_subnet_assign_ipv6_address_on_creation": {
            "value": null
        },
        "database_subnet_group_name": {
            "value": null
        },
        "database_subnet_group_tags": {
            "value": {}
        },
        "database_subnet_ipv6_prefixes": {
            "value": []
        },
        "database_subnet_suffix": {
            "value": "db"
        },
        "database_subnet_tags": {
            "value": {}
        },
        "database_subnets": {
            "value": []
        },
        "default_network_acl_egress": {
            "value": [
                {
                    "action": "allow",
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_no": "100",
                    "to_port": "0"
                },
                {
                    "action": "allow",
                    "from_port": "0",
                    "ipv6_cidr_block": "::/0",
                    "protocol": "-1",
                    "rule_no": "101",
                    "to_port": "0"
                }
            ]
        },
        "default_network_acl_ingress": {
            "value": [
                {
                    "action": "allow",
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_no": "100",
                    "to_port": "0"
                },
                {
                    "action": "allow",
                    "from_port": "0",
                    "ipv6_cidr_block": "::/0",
                    "protocol": "-1",
                    "rule_no": "101",
                    "to_port": "0"
                }
            ]
        },
        "default_network_acl_name": {
            "value": ""
        },
        "default_network_acl_tags": {
            "value": {}
        },
        "default_route_table_propagating_vgws": {
            "value": []
        },
        "default_route_table_routes": {
            "value": []
        },
        "default_route_table_tags": {
            "value": {}
        },
        "default_security_group_egress": {
            "value": null
        },
        "default_security_group_ingress": {
            "value": null
        },
        "default_security_group_name": {
            "value": "default"
        },
        "default_security_group_tags": {
            "value": {}
        },
        "default_vpc_enable_classiclink": {
            "value": false
        },
        "default_vpc_enable_dns_hostnames": {
            "value": false
        },
        "default_vpc_enable_dns_support": {
            "value": true
        },
        "default_vpc_name": {
            "value": ""
        },
        "default_vpc_tags": {
            "value": {}
        },
        "dhcp_options_domain_name": {
            "value": ""
        },
        "dhcp_options_domain_name_servers": {
            "value": [
                "AmazonProvidedDNS"
            ]
        },
        "dhcp_options_netbios_name_servers": {
            "value": []
        },
        "dhcp_options_netbios_node_type": {
            "value": ""
        },
        "dhcp_options_ntp_servers": {
            "value": []
        },
        "dhcp_options_tags": {
            "value": {}
        },
        "elasticache_acl_tags": {
            "value": {}
        },
        "elasticache_dedicated_network_acl": {
            "value": false
        },
        "elasticache_inbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "elasticache_outbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "elasticache_route_table_tags": {
            "value": {}
        },
        "elasticache_subnet_assign_ipv6_address_on_creation": {
            "value": null
        },
        "elasticache_subnet_group_name": {
            "value": null
        },
        "elasticache_subnet_group_tags": {
            "value": {}
        },
        "elasticache_subnet_ipv6_prefixes": {
            "value": []
        },
        "elasticache_subnet_suffix": {
            "value": "elasticache"
        },
        "elasticache_subnet_tags": {
            "value": {}
        },
        "elasticache_subnets": {
            "value": []
        },
        "enable_classiclink": {
            "value": null
        },
        "enable_classiclink_dns_support": {
            "value": null
        },
        "enable_dhcp_options": {
            "value": false
        },
        "enable_dns_hostnames": {
            "value": false
        },
        "enable_dns_support": {
            "value": true
        },
        "enable_flow_log": {
            "value": false
        },
        "enable_ipv6": {
            "value": false
        },
        "enable_nat_gateway": {
            "value": false
        },
        "enable_public_redshift": {
            "value": false
        },
        "enable_vpn_gateway": {
            "value": false
        },
        "external_nat_ip_ids": {
            "value": []
        },
        "external_nat_ips": {
            "value": []
        },
        "flow_log_cloudwatch_iam_role_arn": {
            "value": ""
        },
        "flow_log_cloudwatch_log_group_kms_key_id": {
            "value": null
        },
        "flow_log_cloudwatch_log_group_name_prefix": {
            "value": "/aws/vpc-flow-log/"
        },
        "flow_log_cloudwatch_log_group_retention_in_days": {
            "value": null
        },
        "flow_log_destination_arn": {
            "value": ""
        },
        "flow_log_destination_type": {
            "value": "cloud-watch-logs"
        },
        "flow_log_file_format": {
            "value": "plain-text"
        },
        "flow_log_hive_compatible_partitions": {
            "value": false
        },
        "flow_log_log_format": {
            "value": null
        },
        "flow_log_max_aggregation_interval": {
            "value": 600
        },
        "flow_log_per_hour_partition": {
            "value": false
        },
        "flow_log_traffic_type": {
            "value": "ALL"
        },
        "igw_tags": {
            "value": {}
        },
        "instance_tenancy": {
            "value": "default"
        },
        "intra_acl_tags": {
            "value": {}
        },
        "intra_dedicated_network_acl": {
            "value": false
        },
        "intra_inbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "intra_outbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "intra_route_table_tags": {
            "value": {}
        },
        "intra_subnet_assign_ipv6_address_on_creation": {
            "value": null
        },
        "intra_subnet_ipv6_prefixes": {
            "value": []
        },
        "intra_subnet_suffix": {
            "value": "intra"
        },
        "intra_subnet_tags": {
            "value": {}
        },
        "intra_subnets": {
            "value": []
        },
        "manage_default_network_acl": {
            "value": false
        },
        "manage_default_route_table": {
            "value": false
        },
        "manage_default_security_group": {
            "value": false
        },
        "manage_default_vpc": {
            "value": false
        },
        "map_public_ip_on_launch": {
            "value": true
        },
        "name": {
            "value": ""
        },
        "nat_eip_tags": {
            "value": {}
        },
        "nat_gateway_tags": {
            "value": {}
        },
        "one_nat_gateway_per_az": {
            "value": false
        },
        "outpost_acl_tags": {
            "value": {}
        },
        "outpost_arn": {
            "value": null
        },
        "outpost_az": {
            "value": null
        },
        "outpost_dedicated_network_acl": {
            "value": false
        },
        "outpost_inbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "outpost_outbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "outpost_subnet_assign_ipv6_address_on_creation": {
            "value": null
        },
        "outpost_subnet_ipv6_prefixes": {
            "value": []
        },
        "outpost_subnet_suffix": {
            "value": "outpost"
        },
        "outpost_subnet_tags": {
            "value": {}
        },
        "outpost_subnets": {
            "value": []
        },
        "private_acl_tags": {
            "value": {}
        },
        "private_dedicated_network_acl": {
            "value": false
        },
        "private_inbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "private_outbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "private_route_table_tags": {
            "value": {}
        },
        "private_subnet_assign_ipv6_address_on_creation": {
            "value": null
        },
        "private_subnet_ipv6_prefixes": {
            "value": []
        },
        "private_subnet_suffix": {
            "value": "private"
        },
        "private_subnet_tags": {
            "value": {}
        },
        "private_subnets": {
            "value": []
        },
        "propagate_intra_route_tables_vgw": {
            "value": false
        },
        "propagate_private_route_tables_vgw": {
            "value": false
        },
        "propagate_public_route_tables_vgw": {
            "value": false
        },
        "public_acl_tags": {
            "value": {}
        },
        "public_dedicated_network_acl": {
            "value": false
        },
        "public_inbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "public_outbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "public_route_table_tags": {
            "value": {}
        },
        "public_subnet_assign_ipv6_address_on_creation": {
            "value": null
        },
        "public_subnet_ipv6_prefixes": {
            "value": []
        },
        "public_subnet_suffix": {
            "value": "public"
        },
        "public_subnet_tags": {
            "value": {}
        },
        "public_subnets": {
            "value": []
        },
        "redshift_acl_tags": {
            "value": {}
        },
        "redshift_dedicated_network_acl": {
            "value": false
        },
        "redshift_inbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "redshift_outbound_acl_rules": {
            "value": [
                {
                    "cidr_block": "0.0.0.0/0",
                    "from_port": "0",
                    "protocol": "-1",
                    "rule_action": "allow",
                    "rule_number": "100",
                    "to_port": "0"
                }
            ]
        },
        "redshift_route_table_tags": {
            "value": {}
        },
        "redshift_subnet_assign_ipv6_address_on_creation": {
            "value": null
        },
        "redshift_subnet_group_name": {
            "value": null
        },
        "redshift_subnet_group_tags": {
            "value": {}
        },
        "redshift_subnet_ipv6_prefixes": {
            "value": []
        },
        "redshift_subnet_suffix": {
            "value": "redshift"
        },
        "redshift_subnet_tags": {
            "value": {}
        },
        "redshift_subnets": {
            "value": []
        },
        "reuse_nat_ips": {
            "value": false
        },
        "secondary_cidr_blocks": {
            "value": []
        },
        "single_nat_gateway": {
            "value": false
        },
        "tags": {
            "value": {}
        },
        "vpc_flow_log_permissions_boundary": {
            "value": null
        },
        "vpc_flow_log_tags": {
            "value": {}
        },
        "vpc_tags": {
            "value": {}
        },
        "vpn_gateway_az": {
            "value": null
        },
        "vpn_gateway_id": {
            "value": ""
        },
        "vpn_gateway_tags": {
            "value": {}
        }
    },
    "planned_values": {
        "outputs": {
            "azs": {
                "sensitive": false,
                "value": []
            },
            "cgw_arns": {
                "sensitive": false,
                "value": []
            },
            "cgw_ids": {
                "sensitive": false,
                "value": []
            },
            "database_internet_gateway_route_id": {
                "sensitive": false,
                "value": ""
            },
            "database_ipv6_egress_route_id": {
                "sensitive": false,
                "value": ""
            },
            "database_nat_gateway_route_ids": {
                "sensitive": false,
                "value": []
            },
            "database_network_acl_arn": {
                "sensitive": false,
                "value": ""
            },
            "database_network_acl_id": {
                "sensitive": false,
                "value": ""
            },
            "database_route_table_association_ids": {
                "sensitive": false,
                "value": []
            },
            "database_route_table_ids": {
                "sensitive": false,
                "value": []
            },
            "database_subnet_arns": {
                "sensitive": false,
                "value": []
            },
            "database_subnet_group": {
                "sensitive": false,
                "value": ""
            },
            "database_subnet_group_name": {
                "sensitive": false,
                "value": ""
            },
            "database_subnets": {
                "sensitive": false,
                "value": []
            },
            "database_subnets_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "database_subnets_ipv6_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "default_network_acl_id": {
                "sensitive": false
            },
            "default_route_table_id": {
                "sensitive": false
            },
            "default_security_group_id": {
                "sensitive": false
            },
            "default_vpc_arn": {
                "sensitive": false,
                "value": ""
            },
            "default_vpc_cidr_block": {
                "sensitive": false,
                "value": ""
            },
            "default_vpc_default_network_acl_id": {
                "sensitive": false,
                "value": ""
            },
            "default_vpc_default_route_table_id": {
                "sensitive": false,
                "value": ""
            },
            "default_vpc_default_security_group_id": {
                "sensitive": false,
                "value": ""
            },
            "default_vpc_enable_dns_hostnames": {
                "sensitive": false,
                "value": ""
            },
            "default_vpc_enable_dns_support": {
                "sensitive": false,
                "value": ""
            },
            "default_vpc_id": {
                "sensitive": false,
                "value": ""
            },
            "default_vpc_instance_tenancy": {
                "sensitive": false,
                "value": ""
            },
            "default_vpc_main_route_table_id": {
                "sensitive": false,
                "value": ""
            },
            "dhcp_options_id": {
                "sensitive": false,
                "value": ""
            },
            "egress_only_internet_gateway_id": {
                "sensitive": false,
                "value": ""
            },
            "elasticache_network_acl_arn": {
                "sensitive": false,
                "value": ""
            },
            "elasticache_network_acl_id": {
                "sensitive": false,
                "value": ""
            },
            "elasticache_route_table_association_ids": {
                "sensitive": false,
                "value": []
            },
            "elasticache_route_table_ids": {
                "sensitive": false,
                "value": []
            },
            "elasticache_subnet_arns": {
                "sensitive": false,
                "value": []
            },
            "elasticache_subnet_group": {
                "sensitive": false,
                "value": ""
            },
            "elasticache_subnet_group_name": {
                "sensitive": false,
                "value": ""
            },
            "elasticache_subnets": {
                "sensitive": false,
                "value": []
            },
            "elasticache_subnets_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "elasticache_subnets_ipv6_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "igw_arn": {
                "sensitive": false,
                "value": ""
            },
            "igw_id": {
                "sensitive": false,
                "value": ""
            },
            "intra_network_acl_arn": {
                "sensitive": false,
                "value": ""
            },
            "intra_network_acl_id": {
                "sensitive": false,
                "value": ""
            },
            "intra_route_table_association_ids": {
                "sensitive": false,
                "value": []
            },
            "intra_route_table_ids": {
                "sensitive": false,
                "value": []
            },
            "intra_subnet_arns": {
                "sensitive": false,
                "value": []
            },
            "intra_subnets": {
                "sensitive": false,
                "value": []
            },
            "intra_subnets_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "intra_subnets_ipv6_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "name": {
                "sensitive": false,
                "value": ""
            },
            "nat_ids": {
                "sensitive": false,
                "value": []
            },
            "nat_public_ips": {
                "sensitive": false,
                "value": []
            },
            "natgw_ids": {
                "sensitive": false,
                "value": []
            },
            "outpost_network_acl_arn": {
                "sensitive": false,
                "value": ""
            },
            "outpost_network_acl_id": {
                "sensitive": false,
                "value": ""
            },
            "outpost_subnet_arns": {
                "sensitive": false,
                "value": []
            },
            "outpost_subnets": {
                "sensitive": false,
                "value": []
            },
            "outpost_subnets_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "outpost_subnets_ipv6_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "private_ipv6_egress_route_ids": {
                "sensitive": false,
                "value": []
            },
            "private_nat_gateway_route_ids": {
                "sensitive": false,
                "value": []
            },
            "private_network_acl_arn": {
                "sensitive": false,
                "value": ""
            },
            "private_network_acl_id": {
                "sensitive": false,
                "value": ""
            },
            "private_route_table_association_ids": {
                "sensitive": false,
                "value": []
            },
            "private_route_table_ids": {
                "sensitive": false,
                "value": []
            },
            "private_subnet_arns": {
                "sensitive": false,
                "value": []
            },
            "private_subnets": {
                "sensitive": false,
                "value": []
            },
            "private_subnets_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "private_subnets_ipv6_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "public_internet_gateway_ipv6_route_id": {
                "sensitive": false,
                "value": ""
            },
            "public_internet_gateway_route_id": {
                "sensitive": false,
                "value": ""
            },
            "public_network_acl_arn": {
                "sensitive": false,
                "value": ""
            },
            "public_network_acl_id": {
                "sensitive": false,
                "value": ""
            },
            "public_route_table_association_ids": {
                "sensitive": false,
                "value": []
            },
            "public_route_table_ids": {
                "sensitive": false,
                "value": []
            },
            "public_subnet_arns": {
                "sensitive": false,
                "value": []
            },
            "public_subnets": {
                "sensitive": false,
                "value": []
            },
            "public_subnets_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "public_subnets_ipv6_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "redshift_network_acl_arn": {
                "sensitive": false,
                "value": ""
            },
            "redshift_network_acl_id": {
                "sensitive": false,
                "value": ""
            },
            "redshift_public_route_table_association_ids": {
                "sensitive": false,
                "value": []
            },
            "redshift_route_table_association_ids": {
                "sensitive": false,
                "value": []
            },
            "redshift_route_table_ids": {
                "sensitive": false,
                "value": []
            },
            "redshift_subnet_arns": {
                "sensitive": false,
                "value": []
            },
            "redshift_subnet_group": {
                "sensitive": false,
                "value": ""
            },
            "redshift_subnets": {
                "sensitive": false,
                "value": []
            },
            "redshift_subnets_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "redshift_subnets_ipv6_cidr_blocks": {
                "sensitive": false,
                "value": []
            },
            "this_customer_gateway": {
                "sensitive": false,
                "value": {}
            },
            "vgw_arn": {
                "sensitive": false,
                "value": ""
            },
            "vgw_id": {
                "sensitive": false,
                "value": ""
            },
            "vpc_arn": {
                "sensitive": false
            },
            "vpc_cidr_block": {
                "sensitive": false,
                "value": "10.0.0.0/18"
            },
            "vpc_enable_dns_hostnames": {
                "sensitive": false,
                "value": false
            },
            "vpc_enable_dns_support": {
                "sensitive": false,
                "value": true
            },
            "vpc_flow_log_cloudwatch_iam_role_arn": {
                "sensitive": false,
                "value": ""
            },
            "vpc_flow_log_destination_arn": {
                "sensitive": false,
                "value": ""
            },
            "vpc_flow_log_destination_type": {
                "sensitive": false,
                "value": "cloud-watch-logs"
            },
            "vpc_flow_log_id": {
                "sensitive": false,
                "value": ""
            },
            "vpc_id": {
                "sensitive": false
            },
            "vpc_instance_tenancy": {
                "sensitive": false,
                "value": "default"
            },
            "vpc_ipv6_association_id": {
                "sensitive": false
            },
            "vpc_ipv6_cidr_block": {
                "sensitive": false
            },
            "vpc_main_route_table_id": {
                "sensitive": false
            },
            "vpc_owner_id": {
                "sensitive": false
            },
            "vpc_secondary_cidr_blocks": {
                "sensitive": false,
                "value": []
            }
        },
        "root_module": {
            "resources": [
                {
                    "address": "aws_vpc.this[0]",
                    "mode": "managed",
                    "type": "aws_vpc",
                    "name": "this",
                    "index": 0,
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "schema_version": 1,
                    "values": {
                        "assign_generated_ipv6_cidr_block": false,
                        "cidr_block": "10.0.0.0/18",
                        "enable_dns_hostnames": false,
                        "enable_dns_support": true,
                        "instance_tenancy": "default",
                        "tags": {
                            "Name": ""
                        },
                        "tags_all": {}
                    }
                }
            ]
        }
    },
    "resource_changes": [
        {
            "address": "aws_vpc.this[0]",
            "mode": "managed",
            "type": "aws_vpc",
            "name": "this",
            "index": 0,
            "provider_name": "registry.terraform.io/hashicorp/aws",
            "change": {
                "actions": [
                    "create"
                ],
                "before": null,
                "after": {
                    "assign_generated_ipv6_cidr_block": false,
                    "cidr_block": "10.0.0.0/18",
                    "enable_dns_hostnames": false,
                    "enable_dns_support": true,
                    "instance_tenancy": "default",
                    "tags": {
                        "Name": ""
                    },
                    "tags_all": {}
                },
                "after_unknown": {
                    "arn": true,
                    "default_network_acl_id": true,
                    "default_route_table_id": true,
                    "default_security_group_id": true,
                    "dhcp_options_id": true,
                    "enable_classiclink": true,
                    "enable_classiclink_dns_support": true,
                    "id": true,
                    "ipv6_association_id": true,
                    "ipv6_cidr_block": true,
                    "main_route_table_id": true,
                    "owner_id": true,
                    "tags": {},
                    "tags_all": {
                        "Name": true
                    }
                }
            }
        }
    ],
    "output_changes": {
        "azs": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "cgw_arns": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "cgw_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "database_internet_gateway_route_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "database_ipv6_egress_route_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "database_nat_gateway_route_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "database_network_acl_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "database_network_acl_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "database_route_table_association_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "database_route_table_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "database_subnet_arns": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "database_subnet_group": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "database_subnet_group_name": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "database_subnets": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "database_subnets_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "database_subnets_ipv6_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "default_network_acl_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after_unknown": true
        },
        "default_route_table_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after_unknown": true
        },
        "default_security_group_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after_unknown": true
        },
        "default_vpc_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "default_vpc_cidr_block": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "default_vpc_default_network_acl_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "default_vpc_default_route_table_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "default_vpc_default_security_group_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "default_vpc_enable_dns_hostnames": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "default_vpc_enable_dns_support": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "default_vpc_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "default_vpc_instance_tenancy": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "default_vpc_main_route_table_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "dhcp_options_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "egress_only_internet_gateway_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "elasticache_network_acl_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "elasticache_network_acl_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "elasticache_route_table_association_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "elasticache_route_table_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "elasticache_subnet_arns": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "elasticache_subnet_group": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "elasticache_subnet_group_name": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "elasticache_subnets": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "elasticache_subnets_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "elasticache_subnets_ipv6_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "igw_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "igw_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "intra_network_acl_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "intra_network_acl_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "intra_route_table_association_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "intra_route_table_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "intra_subnet_arns": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "intra_subnets": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "intra_subnets_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "intra_subnets_ipv6_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "name": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "nat_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "nat_public_ips": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "natgw_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "outpost_network_acl_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "outpost_network_acl_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "outpost_subnet_arns": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "outpost_subnets": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "outpost_subnets_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "outpost_subnets_ipv6_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "private_ipv6_egress_route_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "private_nat_gateway_route_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "private_network_acl_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "private_network_acl_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "private_route_table_association_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "private_route_table_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "private_subnet_arns": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "private_subnets": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "private_subnets_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "private_subnets_ipv6_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "public_internet_gateway_ipv6_route_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "public_internet_gateway_route_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "public_network_acl_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "public_network_acl_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "public_route_table_association_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "public_route_table_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "public_subnet_arns": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "public_subnets": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "public_subnets_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "public_subnets_ipv6_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "redshift_network_acl_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "redshift_network_acl_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "redshift_public_route_table_association_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "redshift_route_table_association_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "redshift_route_table_ids": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "redshift_subnet_arns": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "redshift_subnet_group": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "redshift_subnets": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "redshift_subnets_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "redshift_subnets_ipv6_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        },
        "this_customer_gateway": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": {},
            "after_unknown": false
        },
        "vgw_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "vgw_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "vpc_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after_unknown": true
        },
        "vpc_cidr_block": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "10.0.0.0/18",
            "after_unknown": false
        },
        "vpc_enable_dns_hostnames": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": false,
            "after_unknown": false
        },
        "vpc_enable_dns_support": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": true,
            "after_unknown": false
        },
        "vpc_flow_log_cloudwatch_iam_role_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "vpc_flow_log_destination_arn": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "vpc_flow_log_destination_type": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "cloud-watch-logs",
            "after_unknown": false
        },
        "vpc_flow_log_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "",
            "after_unknown": false
        },
        "vpc_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after_unknown": true
        },
        "vpc_instance_tenancy": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": "default",
            "after_unknown": false
        },
        "vpc_ipv6_association_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after_unknown": true
        },
        "vpc_ipv6_cidr_block": {
            "actions": [
                "create"
            ],
            "before": null,
            "after_unknown": true
        },
        "vpc_main_route_table_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after_unknown": true
        },
        "vpc_owner_id": {
            "actions": [
                "create"
            ],
            "before": null,
            "after_unknown": true
        },
        "vpc_secondary_cidr_blocks": {
            "actions": [
                "create"
            ],
            "before": null,
            "after": [],
            "after_unknown": false
        }
    },
    "prior_state": {
        "format_version": "0.1",
        "terraform_version": "0.14.11",
        "values": {
            "outputs": {
                "azs": {
                    "sensitive": false,
                    "value": []
                },
                "cgw_arns": {
                    "sensitive": false,
                    "value": []
                },
                "cgw_ids": {
                    "sensitive": false,
                    "value": []
                },
                "database_internet_gateway_route_id": {
                    "sensitive": false,
                    "value": ""
                },
                "database_ipv6_egress_route_id": {
                    "sensitive": false,
                    "value": ""
                },
                "database_nat_gateway_route_ids": {
                    "sensitive": false,
                    "value": []
                },
                "database_network_acl_arn": {
                    "sensitive": false,
                    "value": ""
                },
                "database_network_acl_id": {
                    "sensitive": false,
                    "value": ""
                },
                "database_route_table_association_ids": {
                    "sensitive": false,
                    "value": []
                },
                "database_route_table_ids": {
                    "sensitive": false,
                    "value": []
                },
                "database_subnet_arns": {
                    "sensitive": false,
                    "value": []
                },
                "database_subnet_group": {
                    "sensitive": false,
                    "value": ""
                },
                "database_subnet_group_name": {
                    "sensitive": false,
                    "value": ""
                },
                "database_subnets": {
                    "sensitive": false,
                    "value": []
                },
                "database_subnets_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "database_subnets_ipv6_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "default_vpc_arn": {
                    "sensitive": false,
                    "value": ""
                },
                "default_vpc_cidr_block": {
                    "sensitive": false,
                    "value": ""
                },
                "default_vpc_default_network_acl_id": {
                    "sensitive": false,
                    "value": ""
                },
                "default_vpc_default_route_table_id": {
                    "sensitive": false,
                    "value": ""
                },
                "default_vpc_default_security_group_id": {
                    "sensitive": false,
                    "value": ""
                },
                "default_vpc_enable_dns_hostnames": {
                    "sensitive": false,
                    "value": ""
                },
                "default_vpc_enable_dns_support": {
                    "sensitive": false,
                    "value": ""
                },
                "default_vpc_id": {
                    "sensitive": false,
                    "value": ""
                },
                "default_vpc_instance_tenancy": {
                    "sensitive": false,
                    "value": ""
                },
                "default_vpc_main_route_table_id": {
                    "sensitive": false,
                    "value": ""
                },
                "dhcp_options_id": {
                    "sensitive": false,
                    "value": ""
                },
                "egress_only_internet_gateway_id": {
                    "sensitive": false,
                    "value": ""
                },
                "elasticache_network_acl_arn": {
                    "sensitive": false,
                    "value": ""
                },
                "elasticache_network_acl_id": {
                    "sensitive": false,
                    "value": ""
                },
                "elasticache_route_table_association_ids": {
                    "sensitive": false,
                    "value": []
                },
                "elasticache_route_table_ids": {
                    "sensitive": false,
                    "value": []
                },
                "elasticache_subnet_arns": {
                    "sensitive": false,
                    "value": []
                },
                "elasticache_subnet_group": {
                    "sensitive": false,
                    "value": ""
                },
                "elasticache_subnet_group_name": {
                    "sensitive": false,
                    "value": ""
                },
                "elasticache_subnets": {
                    "sensitive": false,
                    "value": []
                },
                "elasticache_subnets_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "elasticache_subnets_ipv6_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "igw_arn": {
                    "sensitive": false,
                    "value": ""
                },
                "igw_id": {
                    "sensitive": false,
                    "value": ""
                },
                "intra_network_acl_arn": {
                    "sensitive": false,
                    "value": ""
                },
                "intra_network_acl_id": {
                    "sensitive": false,
                    "value": ""
                },
                "intra_route_table_association_ids": {
                    "sensitive": false,
                    "value": []
                },
                "intra_route_table_ids": {
                    "sensitive": false,
                    "value": []
                },
                "intra_subnet_arns": {
                    "sensitive": false,
                    "value": []
                },
                "intra_subnets": {
                    "sensitive": false,
                    "value": []
                },
                "intra_subnets_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "intra_subnets_ipv6_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "name": {
                    "sensitive": false,
                    "value": ""
                },
                "nat_ids": {
                    "sensitive": false,
                    "value": []
                },
                "nat_public_ips": {
                    "sensitive": false,
                    "value": []
                },
                "natgw_ids": {
                    "sensitive": false,
                    "value": []
                },
                "outpost_network_acl_arn": {
                    "sensitive": false,
                    "value": ""
                },
                "outpost_network_acl_id": {
                    "sensitive": false,
                    "value": ""
                },
                "outpost_subnet_arns": {
                    "sensitive": false,
                    "value": []
                },
                "outpost_subnets": {
                    "sensitive": false,
                    "value": []
                },
                "outpost_subnets_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "outpost_subnets_ipv6_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "private_ipv6_egress_route_ids": {
                    "sensitive": false,
                    "value": []
                },
                "private_nat_gateway_route_ids": {
                    "sensitive": false,
                    "value": []
                },
                "private_network_acl_arn": {
                    "sensitive": false,
                    "value": ""
                },
                "private_network_acl_id": {
                    "sensitive": false,
                    "value": ""
                },
                "private_route_table_association_ids": {
                    "sensitive": false,
                    "value": []
                },
                "private_route_table_ids": {
                    "sensitive": false,
                    "value": []
                },
                "private_subnet_arns": {
                    "sensitive": false,
                    "value": []
                },
                "private_subnets": {
                    "sensitive": false,
                    "value": []
                },
                "private_subnets_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "private_subnets_ipv6_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "public_internet_gateway_ipv6_route_id": {
                    "sensitive": false,
                    "value": ""
                },
                "public_internet_gateway_route_id": {
                    "sensitive": false,
                    "value": ""
                },
                "public_network_acl_arn": {
                    "sensitive": false,
                    "value": ""
                },
                "public_network_acl_id": {
                    "sensitive": false,
                    "value": ""
                },
                "public_route_table_association_ids": {
                    "sensitive": false,
                    "value": []
                },
                "public_route_table_ids": {
                    "sensitive": false,
                    "value": []
                },
                "public_subnet_arns": {
                    "sensitive": false,
                    "value": []
                },
                "public_subnets": {
                    "sensitive": false,
                    "value": []
                },
                "public_subnets_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "public_subnets_ipv6_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "redshift_network_acl_arn": {
                    "sensitive": false,
                    "value": ""
                },
                "redshift_network_acl_id": {
                    "sensitive": false,
                    "value": ""
                },
                "redshift_public_route_table_association_ids": {
                    "sensitive": false,
                    "value": []
                },
                "redshift_route_table_association_ids": {
                    "sensitive": false,
                    "value": []
                },
                "redshift_route_table_ids": {
                    "sensitive": false,
                    "value": []
                },
                "redshift_subnet_arns": {
                    "sensitive": false,
                    "value": []
                },
                "redshift_subnet_group": {
                    "sensitive": false,
                    "value": ""
                },
                "redshift_subnets": {
                    "sensitive": false,
                    "value": []
                },
                "redshift_subnets_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "redshift_subnets_ipv6_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                },
                "this_customer_gateway": {
                    "sensitive": false,
                    "value": {}
                },
                "vgw_arn": {
                    "sensitive": false,
                    "value": ""
                },
                "vgw_id": {
                    "sensitive": false,
                    "value": ""
                },
                "vpc_cidr_block": {
                    "sensitive": false,
                    "value": "10.0.0.0/18"
                },
                "vpc_enable_dns_hostnames": {
                    "sensitive": false,
                    "value": false
                },
                "vpc_enable_dns_support": {
                    "sensitive": false,
                    "value": true
                },
                "vpc_flow_log_cloudwatch_iam_role_arn": {
                    "sensitive": false,
                    "value": ""
                },
                "vpc_flow_log_destination_arn": {
                    "sensitive": false,
                    "value": ""
                },
                "vpc_flow_log_destination_type": {
                    "sensitive": false,
                    "value": "cloud-watch-logs"
                },
                "vpc_flow_log_id": {
                    "sensitive": false,
                    "value": ""
                },
                "vpc_instance_tenancy": {
                    "sensitive": false,
                    "value": "default"
                },
                "vpc_secondary_cidr_blocks": {
                    "sensitive": false,
                    "value": []
                }
            },
            "root_module": {}
        }
    },
    "configuration": {
        "provider_config": {
            "aws": {
                "name": "aws",
                "version_constraint": "\u003e= 3.63.0"
            }
        },
        "root_module": {
            "outputs": {
                "azs": {
                    "expression": {
                        "references": [
                            "var.azs"
                        ]
                    },
                    "description": "A list of availability zones specified as argument to this module"
                },
                "cgw_arns": {
                    "expression": {
                        "references": [
                            "aws_customer_gateway.this"
                        ]
                    },
                    "description": "List of ARNs of Customer Gateway"
                },
                "cgw_ids": {
                    "expression": {
                        "references": [
                            "aws_customer_gateway.this"
                        ]
                    },
                    "description": "List of IDs of Customer Gateway"
                },
                "database_internet_gateway_route_id": {
                    "expression": {
                        "references": [
                            "aws_route.database_internet_gateway"
                        ]
                    },
                    "description": "ID of the database internet gateway route."
                },
                "database_ipv6_egress_route_id": {
                    "expression": {
                        "references": [
                            "aws_route.database_ipv6_egress"
                        ]
                    },
                    "description": "ID of the database IPv6 egress route."
                },
                "database_nat_gateway_route_ids": {
                    "expression": {
                        "references": [
                            "aws_route.database_nat_gateway"
                        ]
                    },
                    "description": "List of IDs of the database nat gateway route."
                },
                "database_network_acl_arn": {
                    "expression": {
                        "references": [
                            "aws_network_acl.database"
                        ]
                    },
                    "description": "ARN of the database network ACL"
                },
                "database_network_acl_id": {
                    "expression": {
                        "references": [
                            "aws_network_acl.database"
                        ]
                    },
                    "description": "ID of the database network ACL"
                },
                "database_route_table_association_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table_association.database"
                        ]
                    },
                    "description": "List of IDs of the database route table association"
                },
                "database_route_table_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table.database",
                            "aws_route_table.database",
                            "aws_route_table.private"
                        ]
                    },
                    "description": "List of IDs of database route tables"
                },
                "database_subnet_arns": {
                    "expression": {
                        "references": [
                            "aws_subnet.database"
                        ]
                    },
                    "description": "List of ARNs of database subnets"
                },
                "database_subnet_group": {
                    "expression": {
                        "references": [
                            "aws_db_subnet_group.database"
                        ]
                    },
                    "description": "ID of database subnet group"
                },
                "database_subnet_group_name": {
                    "expression": {
                        "references": [
                            "aws_db_subnet_group.database"
                        ]
                    },
                    "description": "Name of database subnet group"
                },
                "database_subnets": {
                    "expression": {
                        "references": [
                            "aws_subnet.database"
                        ]
                    },
                    "description": "List of IDs of database subnets"
                },
                "database_subnets_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.database"
                        ]
                    },
                    "description": "List of cidr_blocks of database subnets"
                },
                "database_subnets_ipv6_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.database"
                        ]
                    },
                    "description": "List of IPv6 cidr_blocks of database subnets in an IPv6 enabled VPC"
                },
                "default_network_acl_id": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "The ID of the default network ACL"
                },
                "default_route_table_id": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "The ID of the default route table"
                },
                "default_security_group_id": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "The ID of the security group created by default on VPC creation"
                },
                "default_vpc_arn": {
                    "expression": {
                        "references": [
                            "aws_default_vpc.this"
                        ]
                    },
                    "description": "The ARN of the Default VPC"
                },
                "default_vpc_cidr_block": {
                    "expression": {
                        "references": [
                            "aws_default_vpc.this"
                        ]
                    },
                    "description": "The CIDR block of the Default VPC"
                },
                "default_vpc_default_network_acl_id": {
                    "expression": {
                        "references": [
                            "aws_default_vpc.this"
                        ]
                    },
                    "description": "The ID of the default network ACL of the Default VPC"
                },
                "default_vpc_default_route_table_id": {
                    "expression": {
                        "references": [
                            "aws_default_vpc.this"
                        ]
                    },
                    "description": "The ID of the default route table of the Default VPC"
                },
                "default_vpc_default_security_group_id": {
                    "expression": {
                        "references": [
                            "aws_default_vpc.this"
                        ]
                    },
                    "description": "The ID of the security group created by default on Default VPC creation"
                },
                "default_vpc_enable_dns_hostnames": {
                    "expression": {
                        "references": [
                            "aws_default_vpc.this"
                        ]
                    },
                    "description": "Whether or not the Default VPC has DNS hostname support"
                },
                "default_vpc_enable_dns_support": {
                    "expression": {
                        "references": [
                            "aws_default_vpc.this"
                        ]
                    },
                    "description": "Whether or not the Default VPC has DNS support"
                },
                "default_vpc_id": {
                    "expression": {
                        "references": [
                            "aws_default_vpc.this"
                        ]
                    },
                    "description": "The ID of the Default VPC"
                },
                "default_vpc_instance_tenancy": {
                    "expression": {
                        "references": [
                            "aws_default_vpc.this"
                        ]
                    },
                    "description": "Tenancy of instances spin up within Default VPC"
                },
                "default_vpc_main_route_table_id": {
                    "expression": {
                        "references": [
                            "aws_default_vpc.this"
                        ]
                    },
                    "description": "The ID of the main route table associated with the Default VPC"
                },
                "dhcp_options_id": {
                    "expression": {
                        "references": [
                            "aws_vpc_dhcp_options.this"
                        ]
                    },
                    "description": "The ID of the DHCP options"
                },
                "egress_only_internet_gateway_id": {
                    "expression": {
                        "references": [
                            "aws_egress_only_internet_gateway.this"
                        ]
                    },
                    "description": "The ID of the egress only Internet Gateway"
                },
                "elasticache_network_acl_arn": {
                    "expression": {
                        "references": [
                            "aws_network_acl.elasticache"
                        ]
                    },
                    "description": "ARN of the elasticache network ACL"
                },
                "elasticache_network_acl_id": {
                    "expression": {
                        "references": [
                            "aws_network_acl.elasticache"
                        ]
                    },
                    "description": "ID of the elasticache network ACL"
                },
                "elasticache_route_table_association_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table_association.elasticache"
                        ]
                    },
                    "description": "List of IDs of the elasticache route table association"
                },
                "elasticache_route_table_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table.elasticache",
                            "aws_route_table.elasticache",
                            "aws_route_table.private"
                        ]
                    },
                    "description": "List of IDs of elasticache route tables"
                },
                "elasticache_subnet_arns": {
                    "expression": {
                        "references": [
                            "aws_subnet.elasticache"
                        ]
                    },
                    "description": "List of ARNs of elasticache subnets"
                },
                "elasticache_subnet_group": {
                    "expression": {
                        "references": [
                            "aws_elasticache_subnet_group.elasticache"
                        ]
                    },
                    "description": "ID of elasticache subnet group"
                },
                "elasticache_subnet_group_name": {
                    "expression": {
                        "references": [
                            "aws_elasticache_subnet_group.elasticache"
                        ]
                    },
                    "description": "Name of elasticache subnet group"
                },
                "elasticache_subnets": {
                    "expression": {
                        "references": [
                            "aws_subnet.elasticache"
                        ]
                    },
                    "description": "List of IDs of elasticache subnets"
                },
                "elasticache_subnets_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.elasticache"
                        ]
                    },
                    "description": "List of cidr_blocks of elasticache subnets"
                },
                "elasticache_subnets_ipv6_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.elasticache"
                        ]
                    },
                    "description": "List of IPv6 cidr_blocks of elasticache subnets in an IPv6 enabled VPC"
                },
                "igw_arn": {
                    "expression": {
                        "references": [
                            "aws_internet_gateway.this"
                        ]
                    },
                    "description": "The ARN of the Internet Gateway"
                },
                "igw_id": {
                    "expression": {
                        "references": [
                            "aws_internet_gateway.this"
                        ]
                    },
                    "description": "The ID of the Internet Gateway"
                },
                "intra_network_acl_arn": {
                    "expression": {
                        "references": [
                            "aws_network_acl.intra"
                        ]
                    },
                    "description": "ARN of the intra network ACL"
                },
                "intra_network_acl_id": {
                    "expression": {
                        "references": [
                            "aws_network_acl.intra"
                        ]
                    },
                    "description": "ID of the intra network ACL"
                },
                "intra_route_table_association_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table_association.intra"
                        ]
                    },
                    "description": "List of IDs of the intra route table association"
                },
                "intra_route_table_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table.intra"
                        ]
                    },
                    "description": "List of IDs of intra route tables"
                },
                "intra_subnet_arns": {
                    "expression": {
                        "references": [
                            "aws_subnet.intra"
                        ]
                    },
                    "description": "List of ARNs of intra subnets"
                },
                "intra_subnets": {
                    "expression": {
                        "references": [
                            "aws_subnet.intra"
                        ]
                    },
                    "description": "List of IDs of intra subnets"
                },
                "intra_subnets_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.intra"
                        ]
                    },
                    "description": "List of cidr_blocks of intra subnets"
                },
                "intra_subnets_ipv6_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.intra"
                        ]
                    },
                    "description": "List of IPv6 cidr_blocks of intra subnets in an IPv6 enabled VPC"
                },
                "name": {
                    "expression": {
                        "references": [
                            "var.name"
                        ]
                    },
                    "description": "The name of the VPC specified as argument to this module"
                },
                "nat_ids": {
                    "expression": {
                        "references": [
                            "aws_eip.nat"
                        ]
                    },
                    "description": "List of allocation ID of Elastic IPs created for AWS NAT Gateway"
                },
                "nat_public_ips": {
                    "expression": {
                        "references": [
                            "var.reuse_nat_ips",
                            "var.external_nat_ips",
                            "aws_eip.nat"
                        ]
                    },
                    "description": "List of public Elastic IPs created for AWS NAT Gateway"
                },
                "natgw_ids": {
                    "expression": {
                        "references": [
                            "aws_nat_gateway.this"
                        ]
                    },
                    "description": "List of NAT Gateway IDs"
                },
                "outpost_network_acl_arn": {
                    "expression": {
                        "references": [
                            "aws_network_acl.outpost"
                        ]
                    },
                    "description": "ARN of the outpost network ACL"
                },
                "outpost_network_acl_id": {
                    "expression": {
                        "references": [
                            "aws_network_acl.outpost"
                        ]
                    },
                    "description": "ID of the outpost network ACL"
                },
                "outpost_subnet_arns": {
                    "expression": {
                        "references": [
                            "aws_subnet.outpost"
                        ]
                    },
                    "description": "List of ARNs of outpost subnets"
                },
                "outpost_subnets": {
                    "expression": {
                        "references": [
                            "aws_subnet.outpost"
                        ]
                    },
                    "description": "List of IDs of outpost subnets"
                },
                "outpost_subnets_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.outpost"
                        ]
                    },
                    "description": "List of cidr_blocks of outpost subnets"
                },
                "outpost_subnets_ipv6_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.outpost"
                        ]
                    },
                    "description": "List of IPv6 cidr_blocks of outpost subnets in an IPv6 enabled VPC"
                },
                "private_ipv6_egress_route_ids": {
                    "expression": {
                        "references": [
                            "aws_route.private_ipv6_egress"
                        ]
                    },
                    "description": "List of IDs of the ipv6 egress route."
                },
                "private_nat_gateway_route_ids": {
                    "expression": {
                        "references": [
                            "aws_route.private_nat_gateway"
                        ]
                    },
                    "description": "List of IDs of the private nat gateway route."
                },
                "private_network_acl_arn": {
                    "expression": {
                        "references": [
                            "aws_network_acl.private"
                        ]
                    },
                    "description": "ARN of the private network ACL"
                },
                "private_network_acl_id": {
                    "expression": {
                        "references": [
                            "aws_network_acl.private"
                        ]
                    },
                    "description": "ID of the private network ACL"
                },
                "private_route_table_association_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table_association.private"
                        ]
                    },
                    "description": "List of IDs of the private route table association"
                },
                "private_route_table_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table.private"
                        ]
                    },
                    "description": "List of IDs of private route tables"
                },
                "private_subnet_arns": {
                    "expression": {
                        "references": [
                            "aws_subnet.private"
                        ]
                    },
                    "description": "List of ARNs of private subnets"
                },
                "private_subnets": {
                    "expression": {
                        "references": [
                            "aws_subnet.private"
                        ]
                    },
                    "description": "List of IDs of private subnets"
                },
                "private_subnets_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.private"
                        ]
                    },
                    "description": "List of cidr_blocks of private subnets"
                },
                "private_subnets_ipv6_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.private"
                        ]
                    },
                    "description": "List of IPv6 cidr_blocks of private subnets in an IPv6 enabled VPC"
                },
                "public_internet_gateway_ipv6_route_id": {
                    "expression": {
                        "references": [
                            "aws_route.public_internet_gateway_ipv6"
                        ]
                    },
                    "description": "ID of the IPv6 internet gateway route."
                },
                "public_internet_gateway_route_id": {
                    "expression": {
                        "references": [
                            "aws_route.public_internet_gateway"
                        ]
                    },
                    "description": "ID of the internet gateway route."
                },
                "public_network_acl_arn": {
                    "expression": {
                        "references": [
                            "aws_network_acl.public"
                        ]
                    },
                    "description": "ARN of the public network ACL"
                },
                "public_network_acl_id": {
                    "expression": {
                        "references": [
                            "aws_network_acl.public"
                        ]
                    },
                    "description": "ID of the public network ACL"
                },
                "public_route_table_association_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table_association.public"
                        ]
                    },
                    "description": "List of IDs of the public route table association"
                },
                "public_route_table_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table.public"
                        ]
                    },
                    "description": "List of IDs of public route tables"
                },
                "public_subnet_arns": {
                    "expression": {
                        "references": [
                            "aws_subnet.public"
                        ]
                    },
                    "description": "List of ARNs of public subnets"
                },
                "public_subnets": {
                    "expression": {
                        "references": [
                            "aws_subnet.public"
                        ]
                    },
                    "description": "List of IDs of public subnets"
                },
                "public_subnets_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.public"
                        ]
                    },
                    "description": "List of cidr_blocks of public subnets"
                },
                "public_subnets_ipv6_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.public"
                        ]
                    },
                    "description": "List of IPv6 cidr_blocks of public subnets in an IPv6 enabled VPC"
                },
                "redshift_network_acl_arn": {
                    "expression": {
                        "references": [
                            "aws_network_acl.redshift"
                        ]
                    },
                    "description": "ARN of the redshift network ACL"
                },
                "redshift_network_acl_id": {
                    "expression": {
                        "references": [
                            "aws_network_acl.redshift"
                        ]
                    },
                    "description": "ID of the redshift network ACL"
                },
                "redshift_public_route_table_association_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table_association.redshift_public"
                        ]
                    },
                    "description": "List of IDs of the public redshidt route table association"
                },
                "redshift_route_table_association_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table_association.redshift"
                        ]
                    },
                    "description": "List of IDs of the redshift route table association"
                },
                "redshift_route_table_ids": {
                    "expression": {
                        "references": [
                            "aws_route_table.redshift",
                            "aws_route_table.redshift",
                            "var.enable_public_redshift",
                            "aws_route_table.public",
                            "aws_route_table.private"
                        ]
                    },
                    "description": "List of IDs of redshift route tables"
                },
                "redshift_subnet_arns": {
                    "expression": {
                        "references": [
                            "aws_subnet.redshift"
                        ]
                    },
                    "description": "List of ARNs of redshift subnets"
                },
                "redshift_subnet_group": {
                    "expression": {
                        "references": [
                            "aws_redshift_subnet_group.redshift"
                        ]
                    },
                    "description": "ID of redshift subnet group"
                },
                "redshift_subnets": {
                    "expression": {
                        "references": [
                            "aws_subnet.redshift"
                        ]
                    },
                    "description": "List of IDs of redshift subnets"
                },
                "redshift_subnets_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.redshift"
                        ]
                    },
                    "description": "List of cidr_blocks of redshift subnets"
                },
                "redshift_subnets_ipv6_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_subnet.redshift"
                        ]
                    },
                    "description": "List of IPv6 cidr_blocks of redshift subnets in an IPv6 enabled VPC"
                },
                "this_customer_gateway": {
                    "expression": {
                        "references": [
                            "aws_customer_gateway.this"
                        ]
                    },
                    "description": "Map of Customer Gateway attributes"
                },
                "vgw_arn": {
                    "expression": {
                        "references": [
                            "aws_vpn_gateway.this"
                        ]
                    },
                    "description": "The ARN of the VPN Gateway"
                },
                "vgw_id": {
                    "expression": {
                        "references": [
                            "aws_vpn_gateway.this",
                            "aws_vpn_gateway_attachment.this"
                        ]
                    },
                    "description": "The ID of the VPN Gateway"
                },
                "vpc_arn": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "The ARN of the VPC"
                },
                "vpc_cidr_block": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "The CIDR block of the VPC"
                },
                "vpc_enable_dns_hostnames": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "Whether or not the VPC has DNS hostname support"
                },
                "vpc_enable_dns_support": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "Whether or not the VPC has DNS support"
                },
                "vpc_flow_log_cloudwatch_iam_role_arn": {
                    "expression": {
                        "references": [
                            "local.flow_log_iam_role_arn"
                        ]
                    },
                    "description": "The ARN of the IAM role used when pushing logs to Cloudwatch log group"
                },
                "vpc_flow_log_destination_arn": {
                    "expression": {
                        "references": [
                            "local.flow_log_destination_arn"
                        ]
                    },
                    "description": "The ARN of the destination for VPC Flow Logs"
                },
                "vpc_flow_log_destination_type": {
                    "expression": {
                        "references": [
                            "var.flow_log_destination_type"
                        ]
                    },
                    "description": "The type of the destination for VPC Flow Logs"
                },
                "vpc_flow_log_id": {
                    "expression": {
                        "references": [
                            "aws_flow_log.this"
                        ]
                    },
                    "description": "The ID of the Flow Log resource"
                },
                "vpc_id": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "The ID of the VPC"
                },
                "vpc_instance_tenancy": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "Tenancy of instances spin up within VPC"
                },
                "vpc_ipv6_association_id": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "The association ID for the IPv6 CIDR block"
                },
                "vpc_ipv6_cidr_block": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "The IPv6 CIDR block"
                },
                "vpc_main_route_table_id": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "The ID of the main route table associated with this VPC"
                },
                "vpc_owner_id": {
                    "expression": {
                        "references": [
                            "aws_vpc.this"
                        ]
                    },
                    "description": "The ID of the AWS account that owns the VPC"
                },
                "vpc_secondary_cidr_blocks": {
                    "expression": {
                        "references": [
                            "aws_vpc_ipv4_cidr_block_association.this"
                        ]
                    },
                    "description": "List of secondary CIDR blocks of the VPC"
                }
            },
            "resources": [
                {
                    "address": "aws_cloudwatch_log_group.flow_log",
                    "mode": "managed",
                    "type": "aws_cloudwatch_log_group",
                    "name": "flow_log",
                    "provider_config_key": "aws",
                    "expressions": {
                        "kms_key_id": {
                            "references": [
                                "var.flow_log_cloudwatch_log_group_kms_key_id"
                            ]
                        },
                        "name": {
                            "references": [
                                "var.flow_log_cloudwatch_log_group_name_prefix",
                                "local.vpc_id"
                            ]
                        },
                        "retention_in_days": {
                            "references": [
                                "var.flow_log_cloudwatch_log_group_retention_in_days"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.tags",
                                "var.vpc_flow_log_tags"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "local.create_flow_log_cloudwatch_log_group"
                        ]
                    }
                },
                {
                    "address": "aws_customer_gateway.this",
                    "mode": "managed",
                    "type": "aws_customer_gateway",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "bgp_asn": {
                            "references": [
                                "each.value"
                            ]
                        },
                        "device_name": {
                            "references": [
                                "each.value"
                            ]
                        },
                        "ip_address": {
                            "references": [
                                "each.value"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.name",
                                "each.key",
                                "var.tags",
                                "var.customer_gateway_tags"
                            ]
                        },
                        "type": {
                            "constant_value": "ipsec.1"
                        }
                    },
                    "schema_version": 0,
                    "for_each_expression": {
                        "references": [
                            "var.customer_gateways"
                        ]
                    }
                },
                {
                    "address": "aws_db_subnet_group.database",
                    "mode": "managed",
                    "type": "aws_db_subnet_group",
                    "name": "database",
                    "provider_config_key": "aws",
                    "expressions": {
                        "description": {
                            "references": [
                                "var.name"
                            ]
                        },
                        "name": {
                            "references": [
                                "var.database_subnet_group_name",
                                "var.name"
                            ]
                        },
                        "subnet_ids": {
                            "references": [
                                "aws_subnet.database"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.database_subnet_group_name",
                                "var.name",
                                "var.tags",
                                "var.database_subnet_group_tags"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.database_subnets",
                            "var.create_database_subnet_group"
                        ]
                    }
                },
                {
                    "address": "aws_default_network_acl.this",
                    "mode": "managed",
                    "type": "aws_default_network_acl",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "default_network_acl_id": {
                            "references": [
                                "aws_vpc.this"
                            ]
                        },
                        "subnet_ids": {
                            "references": [
                                "aws_subnet.public",
                                "aws_subnet.private",
                                "aws_subnet.intra",
                                "aws_subnet.database",
                                "aws_subnet.redshift",
                                "aws_subnet.elasticache",
                                "aws_subnet.outpost",
                                "aws_network_acl.public",
                                "aws_network_acl.private",
                                "aws_network_acl.intra",
                                "aws_network_acl.database",
                                "aws_network_acl.redshift",
                                "aws_network_acl.elasticache",
                                "aws_network_acl.outpost"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.default_network_acl_name",
                                "var.tags",
                                "var.default_network_acl_tags"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.manage_default_network_acl"
                        ]
                    }
                },
                {
                    "address": "aws_default_route_table.default",
                    "mode": "managed",
                    "type": "aws_default_route_table",
                    "name": "default",
                    "provider_config_key": "aws",
                    "expressions": {
                        "default_route_table_id": {
                            "references": [
                                "aws_vpc.this[0]"
                            ]
                        },
                        "propagating_vgws": {
                            "references": [
                                "var.default_route_table_propagating_vgws"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.name",
                                "var.tags",
                                "var.default_route_table_tags"
                            ]
                        },
                        "timeouts": {
                            "create": {
                                "constant_value": "5m"
                            },
                            "update": {
                                "constant_value": "5m"
                            }
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.manage_default_route_table"
                        ]
                    }
                },
                {
                    "address": "aws_default_security_group.this",
                    "mode": "managed",
                    "type": "aws_default_security_group",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "tags": {
                            "references": [
                                "var.default_security_group_name",
                                "var.tags",
                                "var.default_security_group_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "aws_vpc.this[0]"
                            ]
                        }
                    },
                    "schema_version": 1,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.manage_default_security_group"
                        ]
                    }
                },
                {
                    "address": "aws_default_vpc.this",
                    "mode": "managed",
                    "type": "aws_default_vpc",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "enable_classiclink": {
                            "references": [
                                "var.default_vpc_enable_classiclink"
                            ]
                        },
                        "enable_dns_hostnames": {
                            "references": [
                                "var.default_vpc_enable_dns_hostnames"
                            ]
                        },
                        "enable_dns_support": {
                            "references": [
                                "var.default_vpc_enable_dns_support"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.default_vpc_name",
                                "var.tags",
                                "var.default_vpc_tags"
                            ]
                        }
                    },
                    "schema_version": 1,
                    "count_expression": {
                        "references": [
                            "var.manage_default_vpc"
                        ]
                    }
                },
                {
                    "address": "aws_egress_only_internet_gateway.this",
                    "mode": "managed",
                    "type": "aws_egress_only_internet_gateway",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "tags": {
                            "references": [
                                "var.name",
                                "var.tags",
                                "var.igw_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.create_egress_only_igw",
                            "var.enable_ipv6",
                            "local.max_subnet_length"
                        ]
                    }
                },
                {
                    "address": "aws_eip.nat",
                    "mode": "managed",
                    "type": "aws_eip",
                    "name": "nat",
                    "provider_config_key": "aws",
                    "expressions": {
                        "tags": {
                            "references": [
                                "var.name",
                                "var.azs",
                                "var.single_nat_gateway",
                                "count.index",
                                "var.tags",
                                "var.nat_eip_tags"
                            ]
                        },
                        "vpc": {
                            "constant_value": true
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.enable_nat_gateway",
                            "var.reuse_nat_ips",
                            "local.nat_gateway_count"
                        ]
                    }
                },
                {
                    "address": "aws_elasticache_subnet_group.elasticache",
                    "mode": "managed",
                    "type": "aws_elasticache_subnet_group",
                    "name": "elasticache",
                    "provider_config_key": "aws",
                    "expressions": {
                        "description": {
                            "references": [
                                "var.name"
                            ]
                        },
                        "name": {
                            "references": [
                                "var.elasticache_subnet_group_name",
                                "var.name"
                            ]
                        },
                        "subnet_ids": {
                            "references": [
                                "aws_subnet.elasticache"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.elasticache_subnet_group_name",
                                "var.name",
                                "var.tags",
                                "var.elasticache_subnet_group_tags"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.elasticache_subnets",
                            "var.create_elasticache_subnet_group"
                        ]
                    }
                },
                {
                    "address": "aws_flow_log.this",
                    "mode": "managed",
                    "type": "aws_flow_log",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "iam_role_arn": {
                            "references": [
                                "local.flow_log_iam_role_arn"
                            ]
                        },
                        "log_destination": {
                            "references": [
                                "local.flow_log_destination_arn"
                            ]
                        },
                        "log_destination_type": {
                            "references": [
                                "var.flow_log_destination_type"
                            ]
                        },
                        "log_format": {
                            "references": [
                                "var.flow_log_log_format"
                            ]
                        },
                        "max_aggregation_interval": {
                            "references": [
                                "var.flow_log_max_aggregation_interval"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.tags",
                                "var.vpc_flow_log_tags"
                            ]
                        },
                        "traffic_type": {
                            "references": [
                                "var.flow_log_traffic_type"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "local.enable_flow_log"
                        ]
                    }
                },
                {
                    "address": "aws_iam_policy.vpc_flow_log_cloudwatch",
                    "mode": "managed",
                    "type": "aws_iam_policy",
                    "name": "vpc_flow_log_cloudwatch",
                    "provider_config_key": "aws",
                    "expressions": {
                        "name_prefix": {
                            "constant_value": "vpc-flow-log-to-cloudwatch-"
                        },
                        "policy": {
                            "references": [
                                "data.aws_iam_policy_document.vpc_flow_log_cloudwatch[0]"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.tags",
                                "var.vpc_flow_log_tags"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "local.create_flow_log_cloudwatch_iam_role"
                        ]
                    }
                },
                {
                    "address": "aws_iam_role.vpc_flow_log_cloudwatch",
                    "mode": "managed",
                    "type": "aws_iam_role",
                    "name": "vpc_flow_log_cloudwatch",
                    "provider_config_key": "aws",
                    "expressions": {
                        "assume_role_policy": {
                            "references": [
                                "data.aws_iam_policy_document.flow_log_cloudwatch_assume_role[0]"
                            ]
                        },
                        "name_prefix": {
                            "constant_value": "vpc-flow-log-role-"
                        },
                        "permissions_boundary": {
                            "references": [
                                "var.vpc_flow_log_permissions_boundary"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.tags",
                                "var.vpc_flow_log_tags"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "local.create_flow_log_cloudwatch_iam_role"
                        ]
                    }
                },
                {
                    "address": "aws_iam_role_policy_attachment.vpc_flow_log_cloudwatch",
                    "mode": "managed",
                    "type": "aws_iam_role_policy_attachment",
                    "name": "vpc_flow_log_cloudwatch",
                    "provider_config_key": "aws",
                    "expressions": {
                        "policy_arn": {
                            "references": [
                                "aws_iam_policy.vpc_flow_log_cloudwatch[0]"
                            ]
                        },
                        "role": {
                            "references": [
                                "aws_iam_role.vpc_flow_log_cloudwatch[0]"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "local.create_flow_log_cloudwatch_iam_role"
                        ]
                    }
                },
                {
                    "address": "aws_internet_gateway.this",
                    "mode": "managed",
                    "type": "aws_internet_gateway",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "tags": {
                            "references": [
                                "var.name",
                                "var.tags",
                                "var.igw_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.create_igw",
                            "var.public_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_nat_gateway.this",
                    "mode": "managed",
                    "type": "aws_nat_gateway",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "allocation_id": {
                            "references": [
                                "local.nat_gateway_ips",
                                "var.single_nat_gateway",
                                "count.index"
                            ]
                        },
                        "subnet_id": {
                            "references": [
                                "aws_subnet.public",
                                "var.single_nat_gateway",
                                "count.index"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.name",
                                "var.azs",
                                "var.single_nat_gateway",
                                "count.index",
                                "var.tags",
                                "var.nat_gateway_tags"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.enable_nat_gateway",
                            "local.nat_gateway_count"
                        ]
                    },
                    "depends_on": [
                        "aws_internet_gateway.this"
                    ]
                },
                {
                    "address": "aws_network_acl.database",
                    "mode": "managed",
                    "type": "aws_network_acl",
                    "name": "database",
                    "provider_config_key": "aws",
                    "expressions": {
                        "subnet_ids": {
                            "references": [
                                "aws_subnet.database"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.database_subnet_suffix",
                                "var.name",
                                "var.tags",
                                "var.database_acl_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "aws_vpc.this"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.database_dedicated_network_acl",
                            "var.database_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl.elasticache",
                    "mode": "managed",
                    "type": "aws_network_acl",
                    "name": "elasticache",
                    "provider_config_key": "aws",
                    "expressions": {
                        "subnet_ids": {
                            "references": [
                                "aws_subnet.elasticache"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.elasticache_subnet_suffix",
                                "var.name",
                                "var.tags",
                                "var.elasticache_acl_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "aws_vpc.this"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.elasticache_dedicated_network_acl",
                            "var.elasticache_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl.intra",
                    "mode": "managed",
                    "type": "aws_network_acl",
                    "name": "intra",
                    "provider_config_key": "aws",
                    "expressions": {
                        "subnet_ids": {
                            "references": [
                                "aws_subnet.intra"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.intra_subnet_suffix",
                                "var.name",
                                "var.tags",
                                "var.intra_acl_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "aws_vpc.this"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.intra_dedicated_network_acl",
                            "var.intra_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl.outpost",
                    "mode": "managed",
                    "type": "aws_network_acl",
                    "name": "outpost",
                    "provider_config_key": "aws",
                    "expressions": {
                        "subnet_ids": {
                            "references": [
                                "aws_subnet.outpost"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.outpost_subnet_suffix",
                                "var.name",
                                "var.tags",
                                "var.outpost_acl_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "aws_vpc.this"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.outpost_dedicated_network_acl",
                            "var.outpost_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl.private",
                    "mode": "managed",
                    "type": "aws_network_acl",
                    "name": "private",
                    "provider_config_key": "aws",
                    "expressions": {
                        "subnet_ids": {
                            "references": [
                                "aws_subnet.private"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.private_subnet_suffix",
                                "var.name",
                                "var.tags",
                                "var.private_acl_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "aws_vpc.this"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.private_dedicated_network_acl",
                            "var.private_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl.public",
                    "mode": "managed",
                    "type": "aws_network_acl",
                    "name": "public",
                    "provider_config_key": "aws",
                    "expressions": {
                        "subnet_ids": {
                            "references": [
                                "aws_subnet.public"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.public_subnet_suffix",
                                "var.name",
                                "var.tags",
                                "var.public_acl_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "aws_vpc.this"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.public_dedicated_network_acl",
                            "var.public_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl.redshift",
                    "mode": "managed",
                    "type": "aws_network_acl",
                    "name": "redshift",
                    "provider_config_key": "aws",
                    "expressions": {
                        "subnet_ids": {
                            "references": [
                                "aws_subnet.redshift"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.redshift_subnet_suffix",
                                "var.name",
                                "var.tags",
                                "var.redshift_acl_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "aws_vpc.this"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.redshift_dedicated_network_acl",
                            "var.redshift_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.database_inbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "database_inbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.database_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": false
                        },
                        "from_port": {
                            "references": [
                                "var.database_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.database_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.database_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.database_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.database[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.database_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.database_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.database_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.database_inbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.database_dedicated_network_acl",
                            "var.database_subnets",
                            "var.database_inbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.database_outbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "database_outbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.database_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": true
                        },
                        "from_port": {
                            "references": [
                                "var.database_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.database_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.database_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.database_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.database[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.database_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.database_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.database_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.database_outbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.database_dedicated_network_acl",
                            "var.database_subnets",
                            "var.database_outbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.elasticache_inbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "elasticache_inbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.elasticache_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": false
                        },
                        "from_port": {
                            "references": [
                                "var.elasticache_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.elasticache_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.elasticache_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.elasticache_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.elasticache[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.elasticache_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.elasticache_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.elasticache_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.elasticache_inbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.elasticache_dedicated_network_acl",
                            "var.elasticache_subnets",
                            "var.elasticache_inbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.elasticache_outbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "elasticache_outbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.elasticache_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": true
                        },
                        "from_port": {
                            "references": [
                                "var.elasticache_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.elasticache_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.elasticache_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.elasticache_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.elasticache[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.elasticache_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.elasticache_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.elasticache_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.elasticache_outbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.elasticache_dedicated_network_acl",
                            "var.elasticache_subnets",
                            "var.elasticache_outbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.intra_inbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "intra_inbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.intra_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": false
                        },
                        "from_port": {
                            "references": [
                                "var.intra_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.intra_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.intra_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.intra_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.intra[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.intra_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.intra_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.intra_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.intra_inbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.intra_dedicated_network_acl",
                            "var.intra_subnets",
                            "var.intra_inbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.intra_outbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "intra_outbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.intra_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": true
                        },
                        "from_port": {
                            "references": [
                                "var.intra_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.intra_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.intra_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.intra_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.intra[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.intra_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.intra_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.intra_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.intra_outbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.intra_dedicated_network_acl",
                            "var.intra_subnets",
                            "var.intra_outbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.outpost_inbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "outpost_inbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.outpost_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": false
                        },
                        "from_port": {
                            "references": [
                                "var.outpost_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.outpost_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.outpost_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.outpost_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.outpost[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.outpost_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.outpost_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.outpost_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.outpost_inbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.outpost_dedicated_network_acl",
                            "var.outpost_subnets",
                            "var.outpost_inbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.outpost_outbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "outpost_outbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.outpost_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": true
                        },
                        "from_port": {
                            "references": [
                                "var.outpost_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.outpost_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.outpost_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.outpost_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.outpost[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.outpost_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.outpost_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.outpost_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.outpost_outbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.outpost_dedicated_network_acl",
                            "var.outpost_subnets",
                            "var.outpost_outbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.private_inbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "private_inbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.private_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": false
                        },
                        "from_port": {
                            "references": [
                                "var.private_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.private_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.private_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.private_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.private[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.private_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.private_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.private_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.private_inbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.private_dedicated_network_acl",
                            "var.private_subnets",
                            "var.private_inbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.private_outbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "private_outbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.private_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": true
                        },
                        "from_port": {
                            "references": [
                                "var.private_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.private_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.private_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.private_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.private[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.private_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.private_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.private_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.private_outbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.private_dedicated_network_acl",
                            "var.private_subnets",
                            "var.private_outbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.public_inbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "public_inbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.public_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": false
                        },
                        "from_port": {
                            "references": [
                                "var.public_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.public_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.public_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.public_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.public[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.public_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.public_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.public_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.public_inbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.public_dedicated_network_acl",
                            "var.public_subnets",
                            "var.public_inbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.public_outbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "public_outbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.public_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": true
                        },
                        "from_port": {
                            "references": [
                                "var.public_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.public_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.public_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.public_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.public[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.public_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.public_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.public_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.public_outbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.public_dedicated_network_acl",
                            "var.public_subnets",
                            "var.public_outbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.redshift_inbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "redshift_inbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.redshift_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": false
                        },
                        "from_port": {
                            "references": [
                                "var.redshift_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.redshift_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.redshift_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.redshift_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.redshift[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.redshift_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.redshift_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.redshift_inbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.redshift_inbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.redshift_dedicated_network_acl",
                            "var.redshift_subnets",
                            "var.redshift_inbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_network_acl_rule.redshift_outbound",
                    "mode": "managed",
                    "type": "aws_network_acl_rule",
                    "name": "redshift_outbound",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.redshift_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "egress": {
                            "constant_value": true
                        },
                        "from_port": {
                            "references": [
                                "var.redshift_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_code": {
                            "references": [
                                "var.redshift_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "icmp_type": {
                            "references": [
                                "var.redshift_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.redshift_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "network_acl_id": {
                            "references": [
                                "aws_network_acl.redshift[0]"
                            ]
                        },
                        "protocol": {
                            "references": [
                                "var.redshift_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_action": {
                            "references": [
                                "var.redshift_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "rule_number": {
                            "references": [
                                "var.redshift_outbound_acl_rules",
                                "count.index"
                            ]
                        },
                        "to_port": {
                            "references": [
                                "var.redshift_outbound_acl_rules",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.redshift_dedicated_network_acl",
                            "var.redshift_subnets",
                            "var.redshift_outbound_acl_rules"
                        ]
                    }
                },
                {
                    "address": "aws_redshift_subnet_group.redshift",
                    "mode": "managed",
                    "type": "aws_redshift_subnet_group",
                    "name": "redshift",
                    "provider_config_key": "aws",
                    "expressions": {
                        "description": {
                            "references": [
                                "var.name"
                            ]
                        },
                        "name": {
                            "references": [
                                "var.redshift_subnet_group_name",
                                "var.name"
                            ]
                        },
                        "subnet_ids": {
                            "references": [
                                "aws_subnet.redshift"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.redshift_subnet_group_name",
                                "var.name",
                                "var.tags",
                                "var.redshift_subnet_group_tags"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.redshift_subnets",
                            "var.create_redshift_subnet_group"
                        ]
                    }
                },
                {
                    "address": "aws_route.database_internet_gateway",
                    "mode": "managed",
                    "type": "aws_route",
                    "name": "database_internet_gateway",
                    "provider_config_key": "aws",
                    "expressions": {
                        "destination_cidr_block": {
                            "constant_value": "0.0.0.0/0"
                        },
                        "gateway_id": {
                            "references": [
                                "aws_internet_gateway.this[0]"
                            ]
                        },
                        "route_table_id": {
                            "references": [
                                "aws_route_table.database[0]"
                            ]
                        },
                        "timeouts": {
                            "create": {
                                "constant_value": "5m"
                            }
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.create_igw",
                            "var.create_database_subnet_route_table",
                            "var.database_subnets",
                            "var.create_database_internet_gateway_route",
                            "var.create_database_nat_gateway_route"
                        ]
                    }
                },
                {
                    "address": "aws_route.database_ipv6_egress",
                    "mode": "managed",
                    "type": "aws_route",
                    "name": "database_ipv6_egress",
                    "provider_config_key": "aws",
                    "expressions": {
                        "destination_ipv6_cidr_block": {
                            "constant_value": "::/0"
                        },
                        "egress_only_gateway_id": {
                            "references": [
                                "aws_egress_only_internet_gateway.this[0]"
                            ]
                        },
                        "route_table_id": {
                            "references": [
                                "aws_route_table.database[0]"
                            ]
                        },
                        "timeouts": {
                            "create": {
                                "constant_value": "5m"
                            }
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.create_egress_only_igw",
                            "var.enable_ipv6",
                            "var.create_database_subnet_route_table",
                            "var.database_subnets",
                            "var.create_database_internet_gateway_route"
                        ]
                    }
                },
                {
                    "address": "aws_route.database_nat_gateway",
                    "mode": "managed",
                    "type": "aws_route",
                    "name": "database_nat_gateway",
                    "provider_config_key": "aws",
                    "expressions": {
                        "destination_cidr_block": {
                            "constant_value": "0.0.0.0/0"
                        },
                        "nat_gateway_id": {
                            "references": [
                                "aws_nat_gateway.this",
                                "count.index"
                            ]
                        },
                        "route_table_id": {
                            "references": [
                                "aws_route_table.database",
                                "count.index"
                            ]
                        },
                        "timeouts": {
                            "create": {
                                "constant_value": "5m"
                            }
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.create_database_subnet_route_table",
                            "var.database_subnets",
                            "var.create_database_internet_gateway_route",
                            "var.create_database_nat_gateway_route",
                            "var.enable_nat_gateway",
                            "var.single_nat_gateway",
                            "var.database_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route.private_ipv6_egress",
                    "mode": "managed",
                    "type": "aws_route",
                    "name": "private_ipv6_egress",
                    "provider_config_key": "aws",
                    "expressions": {
                        "destination_ipv6_cidr_block": {
                            "constant_value": "::/0"
                        },
                        "egress_only_gateway_id": {
                            "references": [
                                "aws_egress_only_internet_gateway.this"
                            ]
                        },
                        "route_table_id": {
                            "references": [
                                "aws_route_table.private",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.create_egress_only_igw",
                            "var.enable_ipv6",
                            "var.private_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route.private_nat_gateway",
                    "mode": "managed",
                    "type": "aws_route",
                    "name": "private_nat_gateway",
                    "provider_config_key": "aws",
                    "expressions": {
                        "destination_cidr_block": {
                            "constant_value": "0.0.0.0/0"
                        },
                        "nat_gateway_id": {
                            "references": [
                                "aws_nat_gateway.this",
                                "count.index"
                            ]
                        },
                        "route_table_id": {
                            "references": [
                                "aws_route_table.private",
                                "count.index"
                            ]
                        },
                        "timeouts": {
                            "create": {
                                "constant_value": "5m"
                            }
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.enable_nat_gateway",
                            "local.nat_gateway_count"
                        ]
                    }
                },
                {
                    "address": "aws_route.public_internet_gateway",
                    "mode": "managed",
                    "type": "aws_route",
                    "name": "public_internet_gateway",
                    "provider_config_key": "aws",
                    "expressions": {
                        "destination_cidr_block": {
                            "constant_value": "0.0.0.0/0"
                        },
                        "gateway_id": {
                            "references": [
                                "aws_internet_gateway.this[0]"
                            ]
                        },
                        "route_table_id": {
                            "references": [
                                "aws_route_table.public[0]"
                            ]
                        },
                        "timeouts": {
                            "create": {
                                "constant_value": "5m"
                            }
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.create_igw",
                            "var.public_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route.public_internet_gateway_ipv6",
                    "mode": "managed",
                    "type": "aws_route",
                    "name": "public_internet_gateway_ipv6",
                    "provider_config_key": "aws",
                    "expressions": {
                        "destination_ipv6_cidr_block": {
                            "constant_value": "::/0"
                        },
                        "gateway_id": {
                            "references": [
                                "aws_internet_gateway.this[0]"
                            ]
                        },
                        "route_table_id": {
                            "references": [
                                "aws_route_table.public[0]"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.create_igw",
                            "var.enable_ipv6",
                            "var.public_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table.database",
                    "mode": "managed",
                    "type": "aws_route_table",
                    "name": "database",
                    "provider_config_key": "aws",
                    "expressions": {
                        "tags": {
                            "references": [
                                "var.single_nat_gateway",
                                "var.create_database_internet_gateway_route",
                                "var.name",
                                "var.database_subnet_suffix",
                                "var.database_subnet_suffix",
                                "var.name",
                                "var.azs",
                                "count.index",
                                "var.tags",
                                "var.database_route_table_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.create_database_subnet_route_table",
                            "var.database_subnets",
                            "var.single_nat_gateway",
                            "var.create_database_internet_gateway_route",
                            "var.database_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table.elasticache",
                    "mode": "managed",
                    "type": "aws_route_table",
                    "name": "elasticache",
                    "provider_config_key": "aws",
                    "expressions": {
                        "tags": {
                            "references": [
                                "var.name",
                                "var.elasticache_subnet_suffix",
                                "var.tags",
                                "var.elasticache_route_table_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.create_elasticache_subnet_route_table",
                            "var.elasticache_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table.intra",
                    "mode": "managed",
                    "type": "aws_route_table",
                    "name": "intra",
                    "provider_config_key": "aws",
                    "expressions": {
                        "tags": {
                            "references": [
                                "var.name",
                                "var.intra_subnet_suffix",
                                "var.tags",
                                "var.intra_route_table_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.intra_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table.private",
                    "mode": "managed",
                    "type": "aws_route_table",
                    "name": "private",
                    "provider_config_key": "aws",
                    "expressions": {
                        "tags": {
                            "references": [
                                "var.single_nat_gateway",
                                "var.name",
                                "var.private_subnet_suffix",
                                "var.private_subnet_suffix",
                                "var.name",
                                "var.azs",
                                "count.index",
                                "var.tags",
                                "var.private_route_table_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "local.max_subnet_length",
                            "local.nat_gateway_count"
                        ]
                    }
                },
                {
                    "address": "aws_route_table.public",
                    "mode": "managed",
                    "type": "aws_route_table",
                    "name": "public",
                    "provider_config_key": "aws",
                    "expressions": {
                        "tags": {
                            "references": [
                                "var.public_subnet_suffix",
                                "var.name",
                                "var.tags",
                                "var.public_route_table_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.public_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table.redshift",
                    "mode": "managed",
                    "type": "aws_route_table",
                    "name": "redshift",
                    "provider_config_key": "aws",
                    "expressions": {
                        "tags": {
                            "references": [
                                "var.name",
                                "var.redshift_subnet_suffix",
                                "var.tags",
                                "var.redshift_route_table_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.create_redshift_subnet_route_table",
                            "var.redshift_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table_association.database",
                    "mode": "managed",
                    "type": "aws_route_table_association",
                    "name": "database",
                    "provider_config_key": "aws",
                    "expressions": {
                        "route_table_id": {
                            "references": [
                                "aws_route_table.database",
                                "aws_route_table.private",
                                "var.create_database_subnet_route_table",
                                "var.single_nat_gateway",
                                "var.create_database_internet_gateway_route",
                                "count.index",
                                "count.index"
                            ]
                        },
                        "subnet_id": {
                            "references": [
                                "aws_subnet.database",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.database_subnets",
                            "var.database_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table_association.elasticache",
                    "mode": "managed",
                    "type": "aws_route_table_association",
                    "name": "elasticache",
                    "provider_config_key": "aws",
                    "expressions": {
                        "route_table_id": {
                            "references": [
                                "aws_route_table.elasticache",
                                "aws_route_table.private",
                                "var.single_nat_gateway",
                                "var.create_elasticache_subnet_route_table",
                                "count.index"
                            ]
                        },
                        "subnet_id": {
                            "references": [
                                "aws_subnet.elasticache",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.elasticache_subnets",
                            "var.elasticache_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table_association.intra",
                    "mode": "managed",
                    "type": "aws_route_table_association",
                    "name": "intra",
                    "provider_config_key": "aws",
                    "expressions": {
                        "route_table_id": {
                            "references": [
                                "aws_route_table.intra"
                            ]
                        },
                        "subnet_id": {
                            "references": [
                                "aws_subnet.intra",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.intra_subnets",
                            "var.intra_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table_association.outpost",
                    "mode": "managed",
                    "type": "aws_route_table_association",
                    "name": "outpost",
                    "provider_config_key": "aws",
                    "expressions": {
                        "route_table_id": {
                            "references": [
                                "aws_route_table.private",
                                "var.single_nat_gateway",
                                "count.index"
                            ]
                        },
                        "subnet_id": {
                            "references": [
                                "aws_subnet.outpost",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.outpost_subnets",
                            "var.outpost_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table_association.private",
                    "mode": "managed",
                    "type": "aws_route_table_association",
                    "name": "private",
                    "provider_config_key": "aws",
                    "expressions": {
                        "route_table_id": {
                            "references": [
                                "aws_route_table.private",
                                "var.single_nat_gateway",
                                "count.index"
                            ]
                        },
                        "subnet_id": {
                            "references": [
                                "aws_subnet.private",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.private_subnets",
                            "var.private_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table_association.public",
                    "mode": "managed",
                    "type": "aws_route_table_association",
                    "name": "public",
                    "provider_config_key": "aws",
                    "expressions": {
                        "route_table_id": {
                            "references": [
                                "aws_route_table.public[0]"
                            ]
                        },
                        "subnet_id": {
                            "references": [
                                "aws_subnet.public",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.public_subnets",
                            "var.public_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table_association.redshift",
                    "mode": "managed",
                    "type": "aws_route_table_association",
                    "name": "redshift",
                    "provider_config_key": "aws",
                    "expressions": {
                        "route_table_id": {
                            "references": [
                                "aws_route_table.redshift",
                                "aws_route_table.private",
                                "var.single_nat_gateway",
                                "var.create_redshift_subnet_route_table",
                                "count.index"
                            ]
                        },
                        "subnet_id": {
                            "references": [
                                "aws_subnet.redshift",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.redshift_subnets",
                            "var.enable_public_redshift",
                            "var.redshift_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_route_table_association.redshift_public",
                    "mode": "managed",
                    "type": "aws_route_table_association",
                    "name": "redshift_public",
                    "provider_config_key": "aws",
                    "expressions": {
                        "route_table_id": {
                            "references": [
                                "aws_route_table.redshift",
                                "aws_route_table.public",
                                "var.single_nat_gateway",
                                "var.create_redshift_subnet_route_table",
                                "count.index"
                            ]
                        },
                        "subnet_id": {
                            "references": [
                                "aws_subnet.redshift",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.redshift_subnets",
                            "var.enable_public_redshift",
                            "var.redshift_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_subnet.database",
                    "mode": "managed",
                    "type": "aws_subnet",
                    "name": "database",
                    "provider_config_key": "aws",
                    "expressions": {
                        "assign_ipv6_address_on_creation": {
                            "references": [
                                "var.database_subnet_assign_ipv6_address_on_creation",
                                "var.assign_ipv6_address_on_creation",
                                "var.database_subnet_assign_ipv6_address_on_creation"
                            ]
                        },
                        "availability_zone": {
                            "references": [
                                "var.azs",
                                "count.index",
                                "var.azs",
                                "count.index"
                            ]
                        },
                        "availability_zone_id": {
                            "references": [
                                "var.azs",
                                "count.index",
                                "var.azs",
                                "count.index"
                            ]
                        },
                        "cidr_block": {
                            "references": [
                                "var.database_subnets",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.enable_ipv6",
                                "var.database_subnet_ipv6_prefixes",
                                "aws_vpc.this[0]",
                                "var.database_subnet_ipv6_prefixes",
                                "count.index"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.database_subnet_suffix",
                                "var.name",
                                "var.azs",
                                "count.index",
                                "var.tags",
                                "var.database_subnet_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 1,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.database_subnets",
                            "var.database_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_subnet.elasticache",
                    "mode": "managed",
                    "type": "aws_subnet",
                    "name": "elasticache",
                    "provider_config_key": "aws",
                    "expressions": {
                        "assign_ipv6_address_on_creation": {
                            "references": [
                                "var.elasticache_subnet_assign_ipv6_address_on_creation",
                                "var.assign_ipv6_address_on_creation",
                                "var.elasticache_subnet_assign_ipv6_address_on_creation"
                            ]
                        },
                        "availability_zone": {
                            "references": [
                                "var.azs",
                                "count.index",
                                "var.azs",
                                "count.index"
                            ]
                        },
                        "availability_zone_id": {
                            "references": [
                                "var.azs",
                                "count.index",
                                "var.azs",
                                "count.index"
                            ]
                        },
                        "cidr_block": {
                            "references": [
                                "var.elasticache_subnets",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.enable_ipv6",
                                "var.elasticache_subnet_ipv6_prefixes",
                                "aws_vpc.this[0]",
                                "var.elasticache_subnet_ipv6_prefixes",
                                "count.index"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.elasticache_subnet_suffix",
                                "var.name",
                                "var.azs",
                                "count.index",
                                "var.tags",
                                "var.elasticache_subnet_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 1,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.elasticache_subnets",
                            "var.elasticache_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_subnet.intra",
                    "mode": "managed",
                    "type": "aws_subnet",
                    "name": "intra",
                    "provider_config_key": "aws",
                    "expressions": {
                        "assign_ipv6_address_on_creation": {
                            "references": [
                                "var.intra_subnet_assign_ipv6_address_on_creation",
                                "var.assign_ipv6_address_on_creation",
                                "var.intra_subnet_assign_ipv6_address_on_creation"
                            ]
                        },
                        "availability_zone": {
                            "references": [
                                "var.azs",
                                "count.index",
                                "var.azs",
                                "count.index"
                            ]
                        },
                        "availability_zone_id": {
                            "references": [
                                "var.azs",
                                "count.index",
                                "var.azs",
                                "count.index"
                            ]
                        },
                        "cidr_block": {
                            "references": [
                                "var.intra_subnets",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.enable_ipv6",
                                "var.intra_subnet_ipv6_prefixes",
                                "aws_vpc.this[0]",
                                "var.intra_subnet_ipv6_prefixes",
                                "count.index"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.intra_subnet_suffix",
                                "var.name",
                                "var.azs",
                                "count.index",
                                "var.tags",
                                "var.intra_subnet_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 1,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.intra_subnets",
                            "var.intra_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_subnet.outpost",
                    "mode": "managed",
                    "type": "aws_subnet",
                    "name": "outpost",
                    "provider_config_key": "aws",
                    "expressions": {
                        "assign_ipv6_address_on_creation": {
                            "references": [
                                "var.outpost_subnet_assign_ipv6_address_on_creation",
                                "var.assign_ipv6_address_on_creation",
                                "var.outpost_subnet_assign_ipv6_address_on_creation"
                            ]
                        },
                        "availability_zone": {
                            "references": [
                                "var.outpost_az"
                            ]
                        },
                        "cidr_block": {
                            "references": [
                                "var.outpost_subnets",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.enable_ipv6",
                                "var.outpost_subnet_ipv6_prefixes",
                                "aws_vpc.this[0]",
                                "var.outpost_subnet_ipv6_prefixes",
                                "count.index"
                            ]
                        },
                        "outpost_arn": {
                            "references": [
                                "var.outpost_arn"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.outpost_subnet_suffix",
                                "var.name",
                                "var.outpost_az",
                                "var.tags",
                                "var.outpost_subnet_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 1,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.outpost_subnets",
                            "var.outpost_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_subnet.private",
                    "mode": "managed",
                    "type": "aws_subnet",
                    "name": "private",
                    "provider_config_key": "aws",
                    "expressions": {
                        "assign_ipv6_address_on_creation": {
                            "references": [
                                "var.private_subnet_assign_ipv6_address_on_creation",
                                "var.assign_ipv6_address_on_creation",
                                "var.private_subnet_assign_ipv6_address_on_creation"
                            ]
                        },
                        "availability_zone": {
                            "references": [
                                "var.azs",
                                "count.index",
                                "var.azs",
                                "count.index"
                            ]
                        },
                        "availability_zone_id": {
                            "references": [
                                "var.azs",
                                "count.index",
                                "var.azs",
                                "count.index"
                            ]
                        },
                        "cidr_block": {
                            "references": [
                                "var.private_subnets",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.enable_ipv6",
                                "var.private_subnet_ipv6_prefixes",
                                "aws_vpc.this[0]",
                                "var.private_subnet_ipv6_prefixes",
                                "count.index"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.private_subnet_suffix",
                                "var.name",
                                "var.azs",
                                "count.index",
                                "var.tags",
                                "var.private_subnet_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 1,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.private_subnets",
                            "var.private_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_subnet.public",
                    "mode": "managed",
                    "type": "aws_subnet",
                    "name": "public",
                    "provider_config_key": "aws",
                    "expressions": {
                        "assign_ipv6_address_on_creation": {
                            "references": [
                                "var.public_subnet_assign_ipv6_address_on_creation",
                                "var.assign_ipv6_address_on_creation",
                                "var.public_subnet_assign_ipv6_address_on_creation"
                            ]
                        },
                        "availability_zone": {
                            "references": [
                                "var.azs",
                                "count.index",
                                "var.azs",
                                "count.index"
                            ]
                        },
                        "availability_zone_id": {
                            "references": [
                                "var.azs",
                                "count.index",
                                "var.azs",
                                "count.index"
                            ]
                        },
                        "cidr_block": {
                            "references": [
                                "var.public_subnets",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.enable_ipv6",
                                "var.public_subnet_ipv6_prefixes",
                                "aws_vpc.this[0]",
                                "var.public_subnet_ipv6_prefixes",
                                "count.index"
                            ]
                        },
                        "map_public_ip_on_launch": {
                            "references": [
                                "var.map_public_ip_on_launch"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.public_subnet_suffix",
                                "var.name",
                                "var.azs",
                                "count.index",
                                "var.tags",
                                "var.public_subnet_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 1,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.public_subnets",
                            "var.one_nat_gateway_per_az",
                            "var.public_subnets",
                            "var.azs",
                            "var.public_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_subnet.redshift",
                    "mode": "managed",
                    "type": "aws_subnet",
                    "name": "redshift",
                    "provider_config_key": "aws",
                    "expressions": {
                        "assign_ipv6_address_on_creation": {
                            "references": [
                                "var.redshift_subnet_assign_ipv6_address_on_creation",
                                "var.assign_ipv6_address_on_creation",
                                "var.redshift_subnet_assign_ipv6_address_on_creation"
                            ]
                        },
                        "availability_zone": {
                            "references": [
                                "var.azs",
                                "count.index",
                                "var.azs",
                                "count.index"
                            ]
                        },
                        "availability_zone_id": {
                            "references": [
                                "var.azs",
                                "count.index",
                                "var.azs",
                                "count.index"
                            ]
                        },
                        "cidr_block": {
                            "references": [
                                "var.redshift_subnets",
                                "count.index"
                            ]
                        },
                        "ipv6_cidr_block": {
                            "references": [
                                "var.enable_ipv6",
                                "var.redshift_subnet_ipv6_prefixes",
                                "aws_vpc.this[0]",
                                "var.redshift_subnet_ipv6_prefixes",
                                "count.index"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.redshift_subnet_suffix",
                                "var.name",
                                "var.azs",
                                "count.index",
                                "var.tags",
                                "var.redshift_subnet_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 1,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.redshift_subnets",
                            "var.redshift_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_vpc.this",
                    "mode": "managed",
                    "type": "aws_vpc",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "assign_generated_ipv6_cidr_block": {
                            "references": [
                                "var.enable_ipv6"
                            ]
                        },
                        "cidr_block": {
                            "references": [
                                "var.cidr"
                            ]
                        },
                        "enable_classiclink": {
                            "references": [
                                "var.enable_classiclink"
                            ]
                        },
                        "enable_classiclink_dns_support": {
                            "references": [
                                "var.enable_classiclink_dns_support"
                            ]
                        },
                        "enable_dns_hostnames": {
                            "references": [
                                "var.enable_dns_hostnames"
                            ]
                        },
                        "enable_dns_support": {
                            "references": [
                                "var.enable_dns_support"
                            ]
                        },
                        "instance_tenancy": {
                            "references": [
                                "var.instance_tenancy"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.name",
                                "var.tags",
                                "var.vpc_tags"
                            ]
                        }
                    },
                    "schema_version": 1,
                    "count_expression": {
                        "references": [
                            "var.create_vpc"
                        ]
                    }
                },
                {
                    "address": "aws_vpc_dhcp_options.this",
                    "mode": "managed",
                    "type": "aws_vpc_dhcp_options",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "domain_name": {
                            "references": [
                                "var.dhcp_options_domain_name"
                            ]
                        },
                        "domain_name_servers": {
                            "references": [
                                "var.dhcp_options_domain_name_servers"
                            ]
                        },
                        "netbios_name_servers": {
                            "references": [
                                "var.dhcp_options_netbios_name_servers"
                            ]
                        },
                        "netbios_node_type": {
                            "references": [
                                "var.dhcp_options_netbios_node_type"
                            ]
                        },
                        "ntp_servers": {
                            "references": [
                                "var.dhcp_options_ntp_servers"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.name",
                                "var.tags",
                                "var.dhcp_options_tags"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.enable_dhcp_options"
                        ]
                    }
                },
                {
                    "address": "aws_vpc_dhcp_options_association.this",
                    "mode": "managed",
                    "type": "aws_vpc_dhcp_options_association",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "dhcp_options_id": {
                            "references": [
                                "aws_vpc_dhcp_options.this[0]"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.enable_dhcp_options"
                        ]
                    }
                },
                {
                    "address": "aws_vpc_ipv4_cidr_block_association.this",
                    "mode": "managed",
                    "type": "aws_vpc_ipv4_cidr_block_association",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "cidr_block": {
                            "references": [
                                "var.secondary_cidr_blocks",
                                "count.index"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "aws_vpc.this[0]"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.secondary_cidr_blocks",
                            "var.secondary_cidr_blocks"
                        ]
                    }
                },
                {
                    "address": "aws_vpn_gateway.this",
                    "mode": "managed",
                    "type": "aws_vpn_gateway",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "amazon_side_asn": {
                            "references": [
                                "var.amazon_side_asn"
                            ]
                        },
                        "availability_zone": {
                            "references": [
                                "var.vpn_gateway_az"
                            ]
                        },
                        "tags": {
                            "references": [
                                "var.name",
                                "var.tags",
                                "var.vpn_gateway_tags"
                            ]
                        },
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.enable_vpn_gateway"
                        ]
                    }
                },
                {
                    "address": "aws_vpn_gateway_attachment.this",
                    "mode": "managed",
                    "type": "aws_vpn_gateway_attachment",
                    "name": "this",
                    "provider_config_key": "aws",
                    "expressions": {
                        "vpc_id": {
                            "references": [
                                "local.vpc_id"
                            ]
                        },
                        "vpn_gateway_id": {
                            "references": [
                                "var.vpn_gateway_id"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.vpn_gateway_id"
                        ]
                    }
                },
                {
                    "address": "aws_vpn_gateway_route_propagation.intra",
                    "mode": "managed",
                    "type": "aws_vpn_gateway_route_propagation",
                    "name": "intra",
                    "provider_config_key": "aws",
                    "expressions": {
                        "route_table_id": {
                            "references": [
                                "aws_route_table.intra",
                                "count.index"
                            ]
                        },
                        "vpn_gateway_id": {
                            "references": [
                                "aws_vpn_gateway.this",
                                "aws_vpn_gateway_attachment.this",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.propagate_intra_route_tables_vgw",
                            "var.enable_vpn_gateway",
                            "var.vpn_gateway_id",
                            "var.intra_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_vpn_gateway_route_propagation.private",
                    "mode": "managed",
                    "type": "aws_vpn_gateway_route_propagation",
                    "name": "private",
                    "provider_config_key": "aws",
                    "expressions": {
                        "route_table_id": {
                            "references": [
                                "aws_route_table.private",
                                "count.index"
                            ]
                        },
                        "vpn_gateway_id": {
                            "references": [
                                "aws_vpn_gateway.this",
                                "aws_vpn_gateway_attachment.this",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.propagate_private_route_tables_vgw",
                            "var.enable_vpn_gateway",
                            "var.vpn_gateway_id",
                            "var.private_subnets"
                        ]
                    }
                },
                {
                    "address": "aws_vpn_gateway_route_propagation.public",
                    "mode": "managed",
                    "type": "aws_vpn_gateway_route_propagation",
                    "name": "public",
                    "provider_config_key": "aws",
                    "expressions": {
                        "route_table_id": {
                            "references": [
                                "aws_route_table.public",
                                "count.index"
                            ]
                        },
                        "vpn_gateway_id": {
                            "references": [
                                "aws_vpn_gateway.this",
                                "aws_vpn_gateway_attachment.this",
                                "count.index"
                            ]
                        }
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "var.create_vpc",
                            "var.propagate_public_route_tables_vgw",
                            "var.enable_vpn_gateway",
                            "var.vpn_gateway_id"
                        ]
                    }
                },
                {
                    "address": "data.aws_iam_policy_document.flow_log_cloudwatch_assume_role",
                    "mode": "data",
                    "type": "aws_iam_policy_document",
                    "name": "flow_log_cloudwatch_assume_role",
                    "provider_config_key": "aws",
                    "expressions": {
                        "statement": [
                            {
                                "actions": {
                                    "constant_value": [
                                        "sts:AssumeRole"
                                    ]
                                },
                                "effect": {
                                    "constant_value": "Allow"
                                },
                                "principals": [
                                    {
                                        "identifiers": {
                                            "constant_value": [
                                                "vpc-flow-logs.amazonaws.com"
                                            ]
                                        },
                                        "type": {
                                            "constant_value": "Service"
                                        }
                                    }
                                ],
                                "sid": {
                                    "constant_value": "AWSVPCFlowLogsAssumeRole"
                                }
                            }
                        ]
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "local.create_flow_log_cloudwatch_iam_role"
                        ]
                    }
                },
                {
                    "address": "data.aws_iam_policy_document.vpc_flow_log_cloudwatch",
                    "mode": "data",
                    "type": "aws_iam_policy_document",
                    "name": "vpc_flow_log_cloudwatch",
                    "provider_config_key": "aws",
                    "expressions": {
                        "statement": [
                            {
                                "actions": {
                                    "constant_value": [
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents",
                                        "logs:DescribeLogGroups",
                                        "logs:DescribeLogStreams"
                                    ]
                                },
                                "effect": {
                                    "constant_value": "Allow"
                                },
                                "resources": {
                                    "constant_value": [
                                        "*"
                                    ]
                                },
                                "sid": {
                                    "constant_value": "AWSVPCFlowLogsPushToCloudWatch"
                                }
                            }
                        ]
                    },
                    "schema_version": 0,
                    "count_expression": {
                        "references": [
                            "local.create_flow_log_cloudwatch_iam_role"
                        ]
                    }
                }
            ],
            "variables": {
                "amazon_side_asn": {
                    "default": "64512",
                    "description": "The Autonomous System Number (ASN) for the Amazon side of the gateway. By default the virtual private gateway is created with the current default Amazon ASN."
                },
                "assign_ipv6_address_on_creation": {
                    "default": false,
                    "description": "Assign IPv6 address on subnet, must be disabled to change IPv6 CIDRs. This is the IPv6 equivalent of map_public_ip_on_launch"
                },
                "azs": {
                    "default": [],
                    "description": "A list of availability zones names or ids in the region"
                },
                "cidr": {
                    "default": "0.0.0.0/0",
                    "description": "The CIDR block for the VPC. Default value is a valid CIDR, but not acceptable by AWS and should be overridden"
                },
                "create_database_internet_gateway_route": {
                    "default": false,
                    "description": "Controls if an internet gateway route for public database access should be created"
                },
                "create_database_nat_gateway_route": {
                    "default": false,
                    "description": "Controls if a nat gateway route should be created to give internet access to the database subnets"
                },
                "create_database_subnet_group": {
                    "default": true,
                    "description": "Controls if database subnet group should be created (n.b. database_subnets must also be set)"
                },
                "create_database_subnet_route_table": {
                    "default": false,
                    "description": "Controls if separate route table for database should be created"
                },
                "create_egress_only_igw": {
                    "default": true,
                    "description": "Controls if an Egress Only Internet Gateway is created and its related routes."
                },
                "create_elasticache_subnet_group": {
                    "default": true,
                    "description": "Controls if elasticache subnet group should be created"
                },
                "create_elasticache_subnet_route_table": {
                    "default": false,
                    "description": "Controls if separate route table for elasticache should be created"
                },
                "create_flow_log_cloudwatch_iam_role": {
                    "default": false,
                    "description": "Whether to create IAM role for VPC Flow Logs"
                },
                "create_flow_log_cloudwatch_log_group": {
                    "default": false,
                    "description": "Whether to create CloudWatch log group for VPC Flow Logs"
                },
                "create_igw": {
                    "default": true,
                    "description": "Controls if an Internet Gateway is created for public subnets and the related routes that connect them."
                },
                "create_redshift_subnet_group": {
                    "default": true,
                    "description": "Controls if redshift subnet group should be created"
                },
                "create_redshift_subnet_route_table": {
                    "default": false,
                    "description": "Controls if separate route table for redshift should be created"
                },
                "create_vpc": {
                    "default": true,
                    "description": "Controls if VPC should be created (it affects almost all resources)"
                },
                "customer_gateway_tags": {
                    "default": {},
                    "description": "Additional tags for the Customer Gateway"
                },
                "customer_gateways": {
                    "default": {},
                    "description": "Maps of Customer Gateway's attributes (BGP ASN and Gateway's Internet-routable external IP address)"
                },
                "database_acl_tags": {
                    "default": {},
                    "description": "Additional tags for the database subnets network ACL"
                },
                "database_dedicated_network_acl": {
                    "default": false,
                    "description": "Whether to use dedicated network ACL (not default) and custom rules for database subnets"
                },
                "database_inbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Database subnets inbound network ACL rules"
                },
                "database_outbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Database subnets outbound network ACL rules"
                },
                "database_route_table_tags": {
                    "default": {},
                    "description": "Additional tags for the database route tables"
                },
                "database_subnet_assign_ipv6_address_on_creation": {
                    "default": null,
                    "description": "Assign IPv6 address on database subnet, must be disabled to change IPv6 CIDRs. This is the IPv6 equivalent of map_public_ip_on_launch"
                },
                "database_subnet_group_name": {
                    "default": null,
                    "description": "Name of database subnet group"
                },
                "database_subnet_group_tags": {
                    "default": {},
                    "description": "Additional tags for the database subnet group"
                },
                "database_subnet_ipv6_prefixes": {
                    "default": [],
                    "description": "Assigns IPv6 database subnet id based on the Amazon provided /56 prefix base 10 integer (0-256). Must be of equal length to the corresponding IPv4 subnet list"
                },
                "database_subnet_suffix": {
                    "default": "db",
                    "description": "Suffix to append to database subnets name"
                },
                "database_subnet_tags": {
                    "default": {},
                    "description": "Additional tags for the database subnets"
                },
                "database_subnets": {
                    "default": [],
                    "description": "A list of database subnets"
                },
                "default_network_acl_egress": {
                    "default": [
                        {
                            "action": "allow",
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_no": "100",
                            "to_port": "0"
                        },
                        {
                            "action": "allow",
                            "from_port": "0",
                            "ipv6_cidr_block": "::/0",
                            "protocol": "-1",
                            "rule_no": "101",
                            "to_port": "0"
                        }
                    ],
                    "description": "List of maps of egress rules to set on the Default Network ACL"
                },
                "default_network_acl_ingress": {
                    "default": [
                        {
                            "action": "allow",
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_no": "100",
                            "to_port": "0"
                        },
                        {
                            "action": "allow",
                            "from_port": "0",
                            "ipv6_cidr_block": "::/0",
                            "protocol": "-1",
                            "rule_no": "101",
                            "to_port": "0"
                        }
                    ],
                    "description": "List of maps of ingress rules to set on the Default Network ACL"
                },
                "default_network_acl_name": {
                    "default": "",
                    "description": "Name to be used on the Default Network ACL"
                },
                "default_network_acl_tags": {
                    "default": {},
                    "description": "Additional tags for the Default Network ACL"
                },
                "default_route_table_propagating_vgws": {
                    "default": [],
                    "description": "List of virtual gateways for propagation"
                },
                "default_route_table_routes": {
                    "default": [],
                    "description": "Configuration block of routes. See https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/default_route_table#route"
                },
                "default_route_table_tags": {
                    "default": {},
                    "description": "Additional tags for the default route table"
                },
                "default_security_group_egress": {
                    "default": null,
                    "description": "List of maps of egress rules to set on the default security group"
                },
                "default_security_group_ingress": {
                    "default": null,
                    "description": "List of maps of ingress rules to set on the default security group"
                },
                "default_security_group_name": {
                    "default": "default",
                    "description": "Name to be used on the default security group"
                },
                "default_security_group_tags": {
                    "default": {},
                    "description": "Additional tags for the default security group"
                },
                "default_vpc_enable_classiclink": {
                    "default": false,
                    "description": "Should be true to enable ClassicLink in the Default VPC"
                },
                "default_vpc_enable_dns_hostnames": {
                    "default": false,
                    "description": "Should be true to enable DNS hostnames in the Default VPC"
                },
                "default_vpc_enable_dns_support": {
                    "default": true,
                    "description": "Should be true to enable DNS support in the Default VPC"
                },
                "default_vpc_name": {
                    "default": "",
                    "description": "Name to be used on the Default VPC"
                },
                "default_vpc_tags": {
                    "default": {},
                    "description": "Additional tags for the Default VPC"
                },
                "dhcp_options_domain_name": {
                    "default": "",
                    "description": "Specifies DNS name for DHCP options set (requires enable_dhcp_options set to true)"
                },
                "dhcp_options_domain_name_servers": {
                    "default": [
                        "AmazonProvidedDNS"
                    ],
                    "description": "Specify a list of DNS server addresses for DHCP options set, default to AWS provided (requires enable_dhcp_options set to true)"
                },
                "dhcp_options_netbios_name_servers": {
                    "default": [],
                    "description": "Specify a list of netbios servers for DHCP options set (requires enable_dhcp_options set to true)"
                },
                "dhcp_options_netbios_node_type": {
                    "default": "",
                    "description": "Specify netbios node_type for DHCP options set (requires enable_dhcp_options set to true)"
                },
                "dhcp_options_ntp_servers": {
                    "default": [],
                    "description": "Specify a list of NTP servers for DHCP options set (requires enable_dhcp_options set to true)"
                },
                "dhcp_options_tags": {
                    "default": {},
                    "description": "Additional tags for the DHCP option set (requires enable_dhcp_options set to true)"
                },
                "elasticache_acl_tags": {
                    "default": {},
                    "description": "Additional tags for the elasticache subnets network ACL"
                },
                "elasticache_dedicated_network_acl": {
                    "default": false,
                    "description": "Whether to use dedicated network ACL (not default) and custom rules for elasticache subnets"
                },
                "elasticache_inbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Elasticache subnets inbound network ACL rules"
                },
                "elasticache_outbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Elasticache subnets outbound network ACL rules"
                },
                "elasticache_route_table_tags": {
                    "default": {},
                    "description": "Additional tags for the elasticache route tables"
                },
                "elasticache_subnet_assign_ipv6_address_on_creation": {
                    "default": null,
                    "description": "Assign IPv6 address on elasticache subnet, must be disabled to change IPv6 CIDRs. This is the IPv6 equivalent of map_public_ip_on_launch"
                },
                "elasticache_subnet_group_name": {
                    "default": null,
                    "description": "Name of elasticache subnet group"
                },
                "elasticache_subnet_group_tags": {
                    "default": {},
                    "description": "Additional tags for the elasticache subnet group"
                },
                "elasticache_subnet_ipv6_prefixes": {
                    "default": [],
                    "description": "Assigns IPv6 elasticache subnet id based on the Amazon provided /56 prefix base 10 integer (0-256). Must be of equal length to the corresponding IPv4 subnet list"
                },
                "elasticache_subnet_suffix": {
                    "default": "elasticache",
                    "description": "Suffix to append to elasticache subnets name"
                },
                "elasticache_subnet_tags": {
                    "default": {},
                    "description": "Additional tags for the elasticache subnets"
                },
                "elasticache_subnets": {
                    "default": [],
                    "description": "A list of elasticache subnets"
                },
                "enable_classiclink": {
                    "default": null,
                    "description": "Should be true to enable ClassicLink for the VPC. Only valid in regions and accounts that support EC2 Classic."
                },
                "enable_classiclink_dns_support": {
                    "default": null,
                    "description": "Should be true to enable ClassicLink DNS Support for the VPC. Only valid in regions and accounts that support EC2 Classic."
                },
                "enable_dhcp_options": {
                    "default": false,
                    "description": "Should be true if you want to specify a DHCP options set with a custom domain name, DNS servers, NTP servers, netbios servers, and/or netbios server type"
                },
                "enable_dns_hostnames": {
                    "default": false,
                    "description": "Should be true to enable DNS hostnames in the VPC"
                },
                "enable_dns_support": {
                    "default": true,
                    "description": "Should be true to enable DNS support in the VPC"
                },
                "enable_flow_log": {
                    "default": false,
                    "description": "Whether or not to enable VPC Flow Logs"
                },
                "enable_ipv6": {
                    "default": false,
                    "description": "Requests an Amazon-provided IPv6 CIDR block with a /56 prefix length for the VPC. You cannot specify the range of IP addresses, or the size of the CIDR block."
                },
                "enable_nat_gateway": {
                    "default": false,
                    "description": "Should be true if you want to provision NAT Gateways for each of your private networks"
                },
                "enable_public_redshift": {
                    "default": false,
                    "description": "Controls if redshift should have public routing table"
                },
                "enable_vpn_gateway": {
                    "default": false,
                    "description": "Should be true if you want to create a new VPN Gateway resource and attach it to the VPC"
                },
                "external_nat_ip_ids": {
                    "default": [],
                    "description": "List of EIP IDs to be assigned to the NAT Gateways (used in combination with reuse_nat_ips)"
                },
                "external_nat_ips": {
                    "default": [],
                    "description": "List of EIPs to be used for `nat_public_ips` output (used in combination with reuse_nat_ips and external_nat_ip_ids)"
                },
                "flow_log_cloudwatch_iam_role_arn": {
                    "default": "",
                    "description": "The ARN for the IAM role that's used to post flow logs to a CloudWatch Logs log group. When flow_log_destination_arn is set to ARN of Cloudwatch Logs, this argument needs to be provided."
                },
                "flow_log_cloudwatch_log_group_kms_key_id": {
                    "default": null,
                    "description": "The ARN of the KMS Key to use when encrypting log data for VPC flow logs."
                },
                "flow_log_cloudwatch_log_group_name_prefix": {
                    "default": "/aws/vpc-flow-log/",
                    "description": "Specifies the name prefix of CloudWatch Log Group for VPC flow logs."
                },
                "flow_log_cloudwatch_log_group_retention_in_days": {
                    "default": null,
                    "description": "Specifies the number of days you want to retain log events in the specified log group for VPC flow logs."
                },
                "flow_log_destination_arn": {
                    "default": "",
                    "description": "The ARN of the CloudWatch log group or S3 bucket where VPC Flow Logs will be pushed. If this ARN is a S3 bucket the appropriate permissions need to be set on that bucket's policy. When create_flow_log_cloudwatch_log_group is set to false this argument must be provided."
                },
                "flow_log_destination_type": {
                    "default": "cloud-watch-logs",
                    "description": "Type of flow log destination. Can be s3 or cloud-watch-logs."
                },
                "flow_log_file_format": {
                    "default": "plain-text",
                    "description": "(Optional) The format for the flow log. Valid values: `plain-text`, `parquet`."
                },
                "flow_log_hive_compatible_partitions": {
                    "default": false,
                    "description": "(Optional) Indicates whether to use Hive-compatible prefixes for flow logs stored in Amazon S3."
                },
                "flow_log_log_format": {
                    "default": null,
                    "description": "The fields to include in the flow log record, in the order in which they should appear."
                },
                "flow_log_max_aggregation_interval": {
                    "default": 600,
                    "description": "The maximum interval of time during which a flow of packets is captured and aggregated into a flow log record. Valid Values: `60` seconds or `600` seconds."
                },
                "flow_log_per_hour_partition": {
                    "default": false,
                    "description": "(Optional) Indicates whether to partition the flow log per hour. This reduces the cost and response time for queries."
                },
                "flow_log_traffic_type": {
                    "default": "ALL",
                    "description": "The type of traffic to capture. Valid values: ACCEPT, REJECT, ALL."
                },
                "igw_tags": {
                    "default": {},
                    "description": "Additional tags for the internet gateway"
                },
                "instance_tenancy": {
                    "default": "default",
                    "description": "A tenancy option for instances launched into the VPC"
                },
                "intra_acl_tags": {
                    "default": {},
                    "description": "Additional tags for the intra subnets network ACL"
                },
                "intra_dedicated_network_acl": {
                    "default": false,
                    "description": "Whether to use dedicated network ACL (not default) and custom rules for intra subnets"
                },
                "intra_inbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Intra subnets inbound network ACLs"
                },
                "intra_outbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Intra subnets outbound network ACLs"
                },
                "intra_route_table_tags": {
                    "default": {},
                    "description": "Additional tags for the intra route tables"
                },
                "intra_subnet_assign_ipv6_address_on_creation": {
                    "default": null,
                    "description": "Assign IPv6 address on intra subnet, must be disabled to change IPv6 CIDRs. This is the IPv6 equivalent of map_public_ip_on_launch"
                },
                "intra_subnet_ipv6_prefixes": {
                    "default": [],
                    "description": "Assigns IPv6 intra subnet id based on the Amazon provided /56 prefix base 10 integer (0-256). Must be of equal length to the corresponding IPv4 subnet list"
                },
                "intra_subnet_suffix": {
                    "default": "intra",
                    "description": "Suffix to append to intra subnets name"
                },
                "intra_subnet_tags": {
                    "default": {},
                    "description": "Additional tags for the intra subnets"
                },
                "intra_subnets": {
                    "default": [],
                    "description": "A list of intra subnets"
                },
                "manage_default_network_acl": {
                    "default": false,
                    "description": "Should be true to adopt and manage Default Network ACL"
                },
                "manage_default_route_table": {
                    "default": false,
                    "description": "Should be true to manage default route table"
                },
                "manage_default_security_group": {
                    "default": false,
                    "description": "Should be true to adopt and manage default security group"
                },
                "manage_default_vpc": {
                    "default": false,
                    "description": "Should be true to adopt and manage Default VPC"
                },
                "map_public_ip_on_launch": {
                    "default": true,
                    "description": "Should be false if you do not want to auto-assign public IP on launch"
                },
                "name": {
                    "default": "",
                    "description": "Name to be used on all the resources as identifier"
                },
                "nat_eip_tags": {
                    "default": {},
                    "description": "Additional tags for the NAT EIP"
                },
                "nat_gateway_tags": {
                    "default": {},
                    "description": "Additional tags for the NAT gateways"
                },
                "one_nat_gateway_per_az": {
                    "default": false,
                    "description": "Should be true if you want only one NAT Gateway per availability zone. Requires `var.azs` to be set, and the number of `public_subnets` created to be greater than or equal to the number of availability zones specified in `var.azs`."
                },
                "outpost_acl_tags": {
                    "default": {},
                    "description": "Additional tags for the outpost subnets network ACL"
                },
                "outpost_arn": {
                    "default": null,
                    "description": "ARN of Outpost you want to create a subnet in."
                },
                "outpost_az": {
                    "default": null,
                    "description": "AZ where Outpost is anchored."
                },
                "outpost_dedicated_network_acl": {
                    "default": false,
                    "description": "Whether to use dedicated network ACL (not default) and custom rules for outpost subnets"
                },
                "outpost_inbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Outpost subnets inbound network ACLs"
                },
                "outpost_outbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Outpost subnets outbound network ACLs"
                },
                "outpost_subnet_assign_ipv6_address_on_creation": {
                    "default": null,
                    "description": "Assign IPv6 address on outpost subnet, must be disabled to change IPv6 CIDRs. This is the IPv6 equivalent of map_public_ip_on_launch"
                },
                "outpost_subnet_ipv6_prefixes": {
                    "default": [],
                    "description": "Assigns IPv6 outpost subnet id based on the Amazon provided /56 prefix base 10 integer (0-256). Must be of equal length to the corresponding IPv4 subnet list"
                },
                "outpost_subnet_suffix": {
                    "default": "outpost",
                    "description": "Suffix to append to outpost subnets name"
                },
                "outpost_subnet_tags": {
                    "default": {},
                    "description": "Additional tags for the outpost subnets"
                },
                "outpost_subnets": {
                    "default": [],
                    "description": "A list of outpost subnets inside the VPC"
                },
                "private_acl_tags": {
                    "default": {},
                    "description": "Additional tags for the private subnets network ACL"
                },
                "private_dedicated_network_acl": {
                    "default": false,
                    "description": "Whether to use dedicated network ACL (not default) and custom rules for private subnets"
                },
                "private_inbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Private subnets inbound network ACLs"
                },
                "private_outbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Private subnets outbound network ACLs"
                },
                "private_route_table_tags": {
                    "default": {},
                    "description": "Additional tags for the private route tables"
                },
                "private_subnet_assign_ipv6_address_on_creation": {
                    "default": null,
                    "description": "Assign IPv6 address on private subnet, must be disabled to change IPv6 CIDRs. This is the IPv6 equivalent of map_public_ip_on_launch"
                },
                "private_subnet_ipv6_prefixes": {
                    "default": [],
                    "description": "Assigns IPv6 private subnet id based on the Amazon provided /56 prefix base 10 integer (0-256). Must be of equal length to the corresponding IPv4 subnet list"
                },
                "private_subnet_suffix": {
                    "default": "private",
                    "description": "Suffix to append to private subnets name"
                },
                "private_subnet_tags": {
                    "default": {},
                    "description": "Additional tags for the private subnets"
                },
                "private_subnets": {
                    "default": [],
                    "description": "A list of private subnets inside the VPC"
                },
                "propagate_intra_route_tables_vgw": {
                    "default": false,
                    "description": "Should be true if you want route table propagation"
                },
                "propagate_private_route_tables_vgw": {
                    "default": false,
                    "description": "Should be true if you want route table propagation"
                },
                "propagate_public_route_tables_vgw": {
                    "default": false,
                    "description": "Should be true if you want route table propagation"
                },
                "public_acl_tags": {
                    "default": {},
                    "description": "Additional tags for the public subnets network ACL"
                },
                "public_dedicated_network_acl": {
                    "default": false,
                    "description": "Whether to use dedicated network ACL (not default) and custom rules for public subnets"
                },
                "public_inbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Public subnets inbound network ACLs"
                },
                "public_outbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Public subnets outbound network ACLs"
                },
                "public_route_table_tags": {
                    "default": {},
                    "description": "Additional tags for the public route tables"
                },
                "public_subnet_assign_ipv6_address_on_creation": {
                    "default": null,
                    "description": "Assign IPv6 address on public subnet, must be disabled to change IPv6 CIDRs. This is the IPv6 equivalent of map_public_ip_on_launch"
                },
                "public_subnet_ipv6_prefixes": {
                    "default": [],
                    "description": "Assigns IPv6 public subnet id based on the Amazon provided /56 prefix base 10 integer (0-256). Must be of equal length to the corresponding IPv4 subnet list"
                },
                "public_subnet_suffix": {
                    "default": "public",
                    "description": "Suffix to append to public subnets name"
                },
                "public_subnet_tags": {
                    "default": {},
                    "description": "Additional tags for the public subnets"
                },
                "public_subnets": {
                    "default": [],
                    "description": "A list of public subnets inside the VPC"
                },
                "redshift_acl_tags": {
                    "default": {},
                    "description": "Additional tags for the redshift subnets network ACL"
                },
                "redshift_dedicated_network_acl": {
                    "default": false,
                    "description": "Whether to use dedicated network ACL (not default) and custom rules for redshift subnets"
                },
                "redshift_inbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Redshift subnets inbound network ACL rules"
                },
                "redshift_outbound_acl_rules": {
                    "default": [
                        {
                            "cidr_block": "0.0.0.0/0",
                            "from_port": "0",
                            "protocol": "-1",
                            "rule_action": "allow",
                            "rule_number": "100",
                            "to_port": "0"
                        }
                    ],
                    "description": "Redshift subnets outbound network ACL rules"
                },
                "redshift_route_table_tags": {
                    "default": {},
                    "description": "Additional tags for the redshift route tables"
                },
                "redshift_subnet_assign_ipv6_address_on_creation": {
                    "default": null,
                    "description": "Assign IPv6 address on redshift subnet, must be disabled to change IPv6 CIDRs. This is the IPv6 equivalent of map_public_ip_on_launch"
                },
                "redshift_subnet_group_name": {
                    "default": null,
                    "description": "Name of redshift subnet group"
                },
                "redshift_subnet_group_tags": {
                    "default": {},
                    "description": "Additional tags for the redshift subnet group"
                },
                "redshift_subnet_ipv6_prefixes": {
                    "default": [],
                    "description": "Assigns IPv6 redshift subnet id based on the Amazon provided /56 prefix base 10 integer (0-256). Must be of equal length to the corresponding IPv4 subnet list"
                },
                "redshift_subnet_suffix": {
                    "default": "redshift",
                    "description": "Suffix to append to redshift subnets name"
                },
                "redshift_subnet_tags": {
                    "default": {},
                    "description": "Additional tags for the redshift subnets"
                },
                "redshift_subnets": {
                    "default": [],
                    "description": "A list of redshift subnets"
                },
                "reuse_nat_ips": {
                    "default": false,
                    "description": "Should be true if you don't want EIPs to be created for your NAT Gateways and will instead pass them in via the 'external_nat_ip_ids' variable"
                },
                "secondary_cidr_blocks": {
                    "default": [],
                    "description": "List of secondary CIDR blocks to associate with the VPC to extend the IP Address pool"
                },
                "single_nat_gateway": {
                    "default": false,
                    "description": "Should be true if you want to provision a single shared NAT Gateway across all of your private networks"
                },
                "tags": {
                    "default": {},
                    "description": "A map of tags to add to all resources"
                },
                "vpc_flow_log_permissions_boundary": {
                    "default": null,
                    "description": "The ARN of the Permissions Boundary for the VPC Flow Log IAM Role"
                },
                "vpc_flow_log_tags": {
                    "default": {},
                    "description": "Additional tags for the VPC Flow Logs"
                },
                "vpc_tags": {
                    "default": {},
                    "description": "Additional tags for the VPC"
                },
                "vpn_gateway_az": {
                    "default": null,
                    "description": "The Availability Zone for the VPN Gateway"
                },
                "vpn_gateway_id": {
                    "default": "",
                    "description": "ID of VPN Gateway to attach to the VPC"
                },
                "vpn_gateway_tags": {
                    "default": {},
                    "description": "Additional tags for the VPN gateway"
                }
            }
        }
    }
}"""
input_data = json.loads(plan_string)
provider_inputs_1 = {
    "input_type": "resource_changes",
    "resource_type": "aws_vpc",
    "attribute": "enable_dns_hostnames",
}

provider_inputs_2 = {
    "input_type": "resource_changes",
    "resource_type": "aws_vpc",
    "attribute": "enable_dns_support",
}


@pytest.mark.passingattr
def test_get_attribute_name_passing():
    res = handler.provide(provider_inputs_1, input_data)
    assert res == [
        {
            "value": False,
            "meta": {
                "address": "aws_vpc.this[0]",
                "mode": "managed",
                "type": "aws_vpc",
                "name": "this",
                "index": 0,
                "provider_name": "registry.terraform.io/hashicorp/aws",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {
                        "assign_generated_ipv6_cidr_block": False,
                        "cidr_block": "10.0.0.0/18",
                        "enable_dns_hostnames": False,
                        "enable_dns_support": True,
                        "instance_tenancy": "default",
                        "tags": {"Name": ""},
                        "tags_all": {},
                    },
                    "after_unknown": {
                        "arn": True,
                        "default_network_acl_id": True,
                        "default_route_table_id": True,
                        "default_security_group_id": True,
                        "dhcp_options_id": True,
                        "enable_classiclink": True,
                        "enable_classiclink_dns_support": True,
                        "id": True,
                        "ipv6_association_id": True,
                        "ipv6_cidr_block": True,
                        "main_route_table_id": True,
                        "owner_id": True,
                        "tags": {},
                        "tags_all": {"Name": True},
                    },
                },
            },
            "err": None,
        }
    ]


@pytest.mark.passingattr
def test_get_attribute_name_passing2():
    res = handler.provide(provider_inputs_1, input_data)
    assert res[0]["value"] == False


@pytest.mark.passingattr
def test_get_attribute_name_passing3():
    res = handler.provide(provider_inputs_2, input_data)
    print(res)
    assert res == [
        {
            "value": True,
            "meta": {
                "address": "aws_vpc.this[0]",
                "mode": "managed",
                "type": "aws_vpc",
                "name": "this",
                "index": 0,
                "provider_name": "registry.terraform.io/hashicorp/aws",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {
                        "assign_generated_ipv6_cidr_block": False,
                        "cidr_block": "10.0.0.0/18",
                        "enable_dns_hostnames": False,
                        "enable_dns_support": True,
                        "instance_tenancy": "default",
                        "tags": {"Name": ""},
                        "tags_all": {},
                    },
                    "after_unknown": {
                        "arn": True,
                        "default_network_acl_id": True,
                        "default_route_table_id": True,
                        "default_security_group_id": True,
                        "dhcp_options_id": True,
                        "enable_classiclink": True,
                        "enable_classiclink_dns_support": True,
                        "id": True,
                        "ipv6_association_id": True,
                        "ipv6_cidr_block": True,
                        "main_route_table_id": True,
                        "owner_id": True,
                        "tags": {},
                        "tags_all": {"Name": True},
                    },
                },
            },
            "err": None,
        }
    ]


@pytest.mark.passingattr
def test_get_attribute_name_passing4():
    res = handler.provide(provider_inputs_2, input_data)
    assert res[0]["value"] == True


@pytest.mark.failingattr
def test_get_attribute_name_failing():
    res = handler.provide(provider_inputs_2, input_data)
    assert res[0]["value"] == False
