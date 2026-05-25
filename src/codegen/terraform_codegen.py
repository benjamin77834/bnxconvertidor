# src/codegen/terraform_codegen.py
"""
Generates Terraform configuration from DAG.
Creates: S3 buckets, Glue jobs, IAM roles, Step Functions, CloudWatch.
"""
from datetime import datetime


def generate_terraform(dag, output_path, xfr_rules=None):
    xfr_rules = xfr_rules or {}
    lines = []

    lines.append(f'# BNX Generated Terraform Configuration')
    lines.append(f'# Generated at: {datetime.now().isoformat()}')
    lines.append(f'# Nodes: {len(dag.execution_order)}')
    lines.append('')

    # Provider
    lines.append('terraform {')
    lines.append('  required_providers {')
    lines.append('    aws = {')
    lines.append('      source  = "hashicorp/aws"')
    lines.append('      version = "~> 5.0"')
    lines.append('    }')
    lines.append('  }')
    lines.append('}')
    lines.append('')
    lines.append('provider "aws" {')
    lines.append('  region = var.aws_region')
    lines.append('}')
    lines.append('')

    # Variables
    lines.append('# ?? Variables ??????????????????????????????????')
    lines.append('variable "aws_region" {')
    lines.append('  default = "us-east-1"')
    lines.append('}')
    lines.append('variable "project_name" {')
    lines.append('  default = "bnx-pipeline"')
    lines.append('}')
    lines.append('variable "environment" {')
    lines.append('  default = "production"')
    lines.append('}')
    lines.append('')

    # S3 Buckets
    lines.append('# ?? S3 Data Lake ?????????????????????????????')
    for bucket in ['raw', 'curated', 'scripts', 'logs']:
        lines.append(f'resource "aws_s3_bucket" "{bucket}" {{')
        lines.append(f'  bucket = "${{var.project_name}}-{bucket}-${{var.environment}}"')
        lines.append(f'  tags = {{')
        lines.append(f'    Project     = var.project_name')
        lines.append(f'    Environment = var.environment')
        lines.append(f'    ManagedBy   = "BNX-Terraform"')
        lines.append(f'  }}')
        lines.append(f'}}')
        lines.append('')
        lines.append(f'resource "aws_s3_bucket_server_side_encryption_configuration" "{bucket}_encryption" {{')
        lines.append(f'  bucket = aws_s3_bucket.{bucket}.id')
        lines.append(f'  rule {{')
        lines.append(f'    apply_server_side_encryption_by_default {{')
        lines.append(f'      sse_algorithm = "aws:kms"')
        lines.append(f'    }}')
        lines.append(f'  }}')
        lines.append(f'}}')
        lines.append('')

    # IAM Role for Glue
    lines.append('# ?? IAM Role for Glue ????????????????????????')
    lines.append('resource "aws_iam_role" "glue_role" {')
    lines.append('  name = "${var.project_name}-glue-role"')
    lines.append('  assume_role_policy = jsonencode({')
    lines.append('    Version = "2012-10-17"')
    lines.append('    Statement = [{')
    lines.append('      Action = "sts:AssumeRole"')
    lines.append('      Effect = "Allow"')
    lines.append('      Principal = { Service = "glue.amazonaws.com" }')
    lines.append('    }]')
    lines.append('  })')
    lines.append('}')
    lines.append('')
    lines.append('resource "aws_iam_role_policy_attachment" "glue_service" {')
    lines.append('  role       = aws_iam_role.glue_role.name')
    lines.append('  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"')
    lines.append('}')
    lines.append('')
    lines.append('resource "aws_iam_role_policy" "glue_s3_access" {')
    lines.append('  name = "s3-access"')
    lines.append('  role = aws_iam_role.glue_role.id')
    lines.append('  policy = jsonencode({')
    lines.append('    Version = "2012-10-17"')
    lines.append('    Statement = [{')
    lines.append('      Effect = "Allow"')
    lines.append('      Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]')
    lines.append('      Resource = [')
    lines.append('        aws_s3_bucket.raw.arn,')
    lines.append('        "${aws_s3_bucket.raw.arn}/*",')
    lines.append('        aws_s3_bucket.curated.arn,')
    lines.append('        "${aws_s3_bucket.curated.arn}/*",')
    lines.append('      ]')
    lines.append('    }]')
    lines.append('  })')
    lines.append('}')
    lines.append('')

    # Glue Catalog Database
    lines.append('# ?? Glue Catalog ?????????????????????????????')
    lines.append('resource "aws_glue_catalog_database" "main" {')
    lines.append('  name = "${var.project_name}_${var.environment}"')
    lines.append('}')
    lines.append('')

    # Glue Jobs ? one per node that is not SOURCE or SINK
    lines.append('# ?? Glue Jobs ??????????????????????????????????')
    graph_boundaries = getattr(dag, 'graph_boundaries', {})
    node_to_graph = {}
    for gname, nids in graph_boundaries.items():
        if "__" not in gname:
            for nid in nids:
                node_to_graph[nid] = gname

    for node in dag.execution_order:
        ntype = node.type.upper()
        if ntype in ('SOURCE', 'SINK'):
            continue
        safe_name = node.id.replace('_', '-')
        lines.append(f'resource "aws_glue_job" "{node.id}" {{')
        lines.append(f'  name     = "${{var.project_name}}-{safe_name}"')
        lines.append(f'  role_arn = aws_iam_role.glue_role.arn')
        lines.append(f'  command {{')
        lines.append(f'    name            = "glueetl"')
        lines.append(f'    script_location = "s3://${{aws_s3_bucket.scripts.bucket}}/jobs/{node.id}.py"')
        lines.append(f'    python_version  = "3"')
        lines.append(f'  }}')
        lines.append(f'  default_arguments = {{')
        lines.append(f'    "--job-language"          = "python"')
        lines.append(f'    "--TempDir"               = "s3://${{aws_s3_bucket.logs.bucket}}/temp/"')
        lines.append(f'    "--enable-metrics"         = "true"')
        lines.append(f'    "--enable-spark-ui"         = "true"')
        lines.append(f'    "--node_type"              = "{ntype}"')
        lines.append(f'  }}')
        lines.append(f'  max_retries       = 1')
        lines.append(f'  timeout           = 60')
        lines.append(f'  number_of_workers = 2')
        lines.append(f'  worker_type       = "G.1X"')
        lines.append(f'  glue_version      = "4.0"')
        lines.append(f'  tags = {{')
        lines.append(f'    NodeType    = "{ntype}"')
        graph_tag = node_to_graph.get(node.id, "")
        if graph_tag:
            lines.append(f'    Graph       = "{graph_tag}"')
        lines.append(f'    ManagedBy   = "BNX-Terraform"')
        lines.append(f'  }}')
        lines.append(f'}}')
        lines.append('')

    # CloudWatch Alarms
    lines.append('# ?? CloudWatch Alarms ????????????????????????')
    lines.append('resource "aws_sns_topic" "alerts" {')
    lines.append('  name = "${var.project_name}-alerts"')
    lines.append('}')
    lines.append('')

    # Outputs
    lines.append('# ?? Outputs ??????????????????????????????????')
    lines.append('output "raw_bucket" { value = aws_s3_bucket.raw.bucket }')
    lines.append('output "curated_bucket" { value = aws_s3_bucket.curated.bucket }')
    lines.append('output "glue_role_arn" { value = aws_iam_role.glue_role.arn }')
    lines.append('output "catalog_database" { value = aws_glue_catalog_database.main.name }')
    lines.append(f'output "total_glue_jobs" {{ value = {sum(1 for n in dag.execution_order if n.type.upper() not in ("SOURCE","SINK"))} }}')

    with open(output_path, "w") as f:
        f.write('\n'.join(lines))

    return '\n'.join(lines)
