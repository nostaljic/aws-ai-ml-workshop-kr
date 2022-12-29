# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
"""A CLI to create or update and run pipelines."""
from __future__ import absolute_import

import argparse
import json
import sys
import traceback

from pipelines._utils import get_pipeline_driver, convert_struct, get_pipeline_custom_tags


def main():  # pragma: no cover
    """The main harness that creates or updates and runs the pipeline.

    Creates or updates the pipeline and runs it.
    """
    parser = argparse.ArgumentParser(
        "Creates or updates and runs the pipeline for the pipeline script."
    )

    parser.add_argument(
        "-n",
        "--module-name",
        dest="module_name",
        type=str,
        help="The module name of the pipeline to import.",
    )
    parser.add_argument(
        "-kwargs",
        "--kwargs",
        dest="kwargs",
        default=None,
        help="Dict string of keyword arguments for the pipeline generation (if supported)",
    )
    parser.add_argument(
        "-role-arn",
        "--role-arn",
        dest="role_arn",
        type=str,
        help="The role arn for the pipeline service execution role.",
    )
    parser.add_argument(
        "-description",
        "--description",
        dest="description",
        type=str,
        default=None,
        help="The description of the pipeline.",
    )
    parser.add_argument(
        "-tags",
        "--tags",
        dest="tags",
        default=None,
        help="""List of dict strings of '[{"Key": "string", "Value": "string"}, ..]'""",
    )
    print("###### Staring in run_pipeline by gs ############:")

    
    args = parser.parse_args()

    if args.module_name is None or args.role_arn is None:
        parser.print_help()
        sys.exit(2)


    try:
        
        ##################################
        # pipeline 오브젝트 얻기
        ##################################        
        
        import json
        
        pipeline = get_pipeline_driver(args.module_name, args.kwargs)
        print("###### Creating/updating a SageMaker Pipeline with the following definition:")
        parsed = json.loads(pipeline.definition())
        print(json.dumps(parsed, indent=2, sort_keys=True))

        upsert_response = pipeline.upsert(
            role_arn=args.role_arn, description=args.description)

        
        print("\n###### Created/Updated SageMaker Pipeline: Response received:")
        print(upsert_response)

        
        ##################################
        # 설정 파일에서 변수 값을 가져온다.
        ##################################        
        
        print("\n ###### Loading config variables for running a  parametized pipeline:")
        
        sm_pipeline_train_config_json_path = 'pipelines/ncf/src/sm_pipeline_train_config.json'

        from pipelines.ncf.src.common_utils import load_json
        
        sm_pipeline_train_dict = load_json(sm_pipeline_train_config_json_path)

        import json
        print("SageMaker Pipeline Series Params: ")
        print (json.dumps(sm_pipeline_train_dict, indent=2))


        s3_input_data_uri = sm_pipeline_train_dict["s3_input_data_uri"]
        training_instance_type = sm_pipeline_train_dict["training_instance_type"]
        training_instance_count = sm_pipeline_train_dict["training_instance_count"]
        ModelApprovalStatus = sm_pipeline_train_dict["ModelApprovalStatus"] 
        inference_image_uri = sm_pipeline_train_dict["inference_image_uri"]
    
        print(f"s3_input_data_uri: {s3_input_data_uri}")            
        print(f"training_instance_type: {training_instance_type}")
        print(f"training_instance_count: {training_instance_count}")
        print(f"ModelApprovalStatus: {ModelApprovalStatus}")
        print(f"inference_image_uri: {inference_image_uri}")        
    
        ##################################
        # 파라미터를 가지고 파이프라인 실행
        ##################################        
    
    
        execution = pipeline.start(
            parameters=dict(
                InputData= s3_input_data_uri,
                training_instance_type = training_instance_type,
                training_instance_count = training_instance_count,
                ModelApprovalStatus = ModelApprovalStatus,            
                inference_image_uri = inference_image_uri,     
            )
        )        

        print(f"\n###### Execution started with PipelineExecutionArn: {execution.arn}")

        print("Waiting for the execution to finish...")

        # Setting the attempts and delay (in seconds) will modify the overall time the pipeline waits. 
        # If the execution is taking a longer time, update these parameters to a larger value.
        # Eg: The total wait time is calculated as 60 * 120 = 7200 seconds (2 hours)
        execution.wait(max_attempts=120, delay=60)
        
        print("\n#####Execution completed. Execution step details:")

        print(execution.list_steps())
        # Todo print the status?
    except Exception as e:  # pylint: disable=W0703
        print(f"Exception: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
