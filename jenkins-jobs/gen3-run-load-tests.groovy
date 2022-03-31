/*
  String parameter TARGET_ENVIRONMENT
    e.g., qa-dcp
  Choice parameter LOAD_TEST_DESCRIPTOR
    Values: fence-presigned-url
            create-indexd-records
            sheepdog-import-clinical-metada
            metadata-service-create-and-query
            metadata-service-filter-large-database
            study-viewer
            audit-presigned-url
            audit-login

  String parameter PRESIGNED_URL_ACL_FILTER
    Default value: QA
  String parameter SHEEPDOG_NUM_OF_RECORDS_TO_IMPORT
    Default value: 100
  String parameter DESIRED_NUMBER_OF_FENCE_PODS
    Default value: 10
  String parameter RELEASE_VERSION
    e.g., 2021.04
  String parameter INDEXD_NUM_OF_RECORDS_TO_CREATE
    e.g., 10000
  String parameter SIGNED_URL_PROTOCOL
    e.g., s3
  String parameter SQS_URL
    e.g., https://sqs.us-east-1.amazonaws.com/707767160287/qaplanetv2--qa-niaid--audit-sqs

*/

pipeline {
    agent { node { label 'gen3-qa-worker' } }
    // agent { node { label 'master' } }
    stages {
        stage('Clean workspace') {
            steps {
                cleanWs()
            }
        }
        stage('Checkout source') {
            steps {
                // cloud-automation
                checkout([
                  $class: 'GitSCM',
                  branches: [[name: 'refs/heads/master']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'cloud-automation']],
                  submoduleCfg: [],
                  userRemoteConfigs: [[credentialsId: 'PlanXCyborgUser', url: 'https://github.com/uc-cdis/cloud-automation.git']]
                ])
                // gen3-qa
                checkout([
                  $class: 'GitSCM',
                  branches: [[name: 'refs/heads/master']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'gen3-qa']],
                  submoduleCfg: [],
                  userRemoteConfigs: [[credentialsId: 'PlanXCyborgUser', url: 'https://github.com/uc-cdis/gen3-qa.git']]
                ])
            }
        }
        stage('create test data (TODO)') {
            steps {
                sh """
                  mkdir -p testData
                """
            }
        }
        stage('Setup for Load Tests') {
            steps {
                withCredentials([
                  file(credentialsId: 'qa-dcp-credentials-json', variable: 'QA_DCP_CREDS_JSON')
                ]){
                sh """#!/bin/bash

                  export KUBECTL_NAMESPACE="$TARGET_ENVIRONMENT"
                  # setup gen3 CLI
                  export GEN3_HOME=\$WORKSPACE/cloud-automation
                  source \$GEN3_HOME/gen3/gen3setup.sh

                  indexdRecord=$(curl https://$KUBECTL_NAMESPACE/index/index | jq -r '.records | length')
                  if [[ ${indexdRecord} -lt 0 ]];
                    curl -X POST 'https://$KUBECTL_NAMESPACE/index/index' -H "$QA_DCP_CREDS_JSON" -H "Content-Type: application/json" -d \
                      '{"acl":[],"authz":["/abc/programs"],"file_name":"qa-test.txt","form":"object","hash":{"mds":"404e8919021a03285697647487f528ef"},"size":2681688756,"urls":["gs://dcf-integration-qa/qa-test.txt", "s3://cdis-presigned-url-test/testdata"]}' #pragma: allowlist secret
                  else
                    echo "There are more than 1 record in indexd. We should be good to go .."

                  if [ "$LOAD_TEST_DESCRIPTOR" == "audit-presigned-url" ]; then
                    echo "Populating audit-service SQS with presigned-url messages"
                    bash gen3-qa/load-testing/audit-service/sendPresignedURLMessages.sh $SQS_URL
                  elif [ "$LOAD_TEST_DESCRIPTOR" == "audit-login" ]; then
                    echo "Populating audit-service SQS with login messages"
                    bash gen3-qa/load-testing/audit-service/sendLoginMessages.sh $SQS_URL
                  elif [ "$LOAD_TEST_DESCRIPTOR" == "fence-presigned-url" ]; then
                    # This is not working
                    # We should use "gen3 gitops configmaps scaling && gen3 scaling apply all" instead.
                    # gen3 replicas presigned-url-fence $DESIRED_NUMBER_OF_FENCE_PODS
                    gen3 scaling update presigned-url-fence 6 10 14
                    sleep 60
                    g3kubectl get pods | grep fence
                  else
                    echo "Presigned URL test was not selected. Skipping auto-scaling changes..."
                  fi
                """
            }}
        }
        stage('run tests') {
            environment {
                JENKINS_PATH = sh(script: 'pwd', , returnStdout: true).trim()
            }
            steps {
                withCredentials([
                  file(credentialsId: 'fence-google-app-creds-secret', variable: 'GOOGLE_APP_CREDS_JSON'),
                  file(credentialsId: 'qa-dcp-credentials-json', variable: 'QA_DCP_CREDS_JSON'),
                  file(credentialsId: 'ed-dev-environment-credentials', variable: 'ED_DEV_ENV_CREDS_JSON'),
                  string(credentialsId: 'temporary-qa-dcp-long-living-access-token', variable: 'ACCESS_TOKEN'),
                  file(credentialsId: 'QA-NIAID-CRED', variable: 'QA_NIAID_CREDS'),
                  file(credentialsId: 'CTDS_TEST_ENV_MTLS_CERT', variable: 'CTDS_TEST_ENV_MTLS_CERT'),
                  file(credentialsId: 'CTDS_TEST_ENV_MTLS_KEY', variable: 'CTDS_TEST_ENV_MTLS_KEY'),
                  file(credentialsId: 'QA_DCP_MTLS_CERT', variable: 'QA_DCP_MTLS_CERT'),
                  file(credentialsId: 'QA_DCP_MTLS_KEY', variable: 'QA_DCP_MTLS_KEY'),
                  file(credentialsId: 'CTDS_TEST_ENV_CREDS_JSON', variable: 'CTDS_TEST_ENV_CREDS_JSON')
                ]){
                  dir("gen3-qa") {
                      script {
                        def selectedLoadTestDescriptor = LOAD_TEST_DESCRIPTOR
                        sh """#!/bin/bash -x

                          export GEN3_HOME=../cloud-automation
                          export TEST_DATA_PATH=../testData
                          export GEN3_SKIP_PROJ_SETUP=true
                          export RUNNING_LOCAL=false

                          mv "$QA_DCP_CREDS_JSON" credentials.json

                          npm install

                          SELECTED_LOAD_TEST_DESCRIPTOR=""

                          if [ "$TARGET_ENVIRONMENT" == "qa-dcp" ]; then
                            echo "b/c target env is qa-dcp, using qa-dcp mLTS client cert and tokens"
                            mv "$QA_DCP_MTLS_CERT" "\$JENKINS_PATH/mtls.crt"
                            mv "$QA_DCP_MTLS_KEY" "\$JENKINS_PATH/mtls.key"
                          elif [ "$TARGET_ENVIRONMENT" == "ctds-test-env" ]; then
                            echo "b/c target env is ctds-test-env, we'll use the ctds-test-env mLTS client cert and tokens"
                            mv "$CTDS_TEST_ENV_MTLS_CERT" "\$JENKINS_PATH/mtls.crt"
                            mv "$CTDS_TEST_ENV_MTLS_KEY" "\$JENKINS_PATH/mtls.key"
                            mv "$CTDS_TEST_ENV_CREDS_JSON" credentials.json
                          else
                            echo "configured ctds-test-env mTLS by default b/c you did not choose a TARGET_ENVIRONMENT which has configured mTLS creds"
                            mv "$CTDS_TEST_ENV_MTLS_CERT" "\$JENKINS_PATH/mtls.crt"
                            mv "$CTDS_TEST_ENV_MTLS_KEY" "\$JENKINS_PATH/mtls.key"
                          fi

                          # TODO: Make this work
                          # case statement to use one of the load test descriptor JSON files
                          case $selectedLoadTestDescriptor in
                          fence-presigned-url)
                              echo "Selected presigned url"
                              # FOR PRESIGNED URLS
                              sed -i 's/"indexd_record_acl": "phs000178",/"indexd_record_acl": "$PRESIGNED_URL_ACL_FILTER",/' load-testing/sample-descriptors/load-test-presigned-url-bottleneck-sample.json
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-presigned-url-bottleneck-sample.json random-guids"
                              ;;
                          fence-presigned-url-stress-test)
                              echo "Selected presigned url stress test"
                              # FOR PRESIGNED URLS
                              sed -i 's/"indexd_record_acl": "phs000178",/"indexd_record_acl": "$PRESIGNED_URL_ACL_FILTER",/' load-testing/sample-descriptors/presigned-url-stress-test.json
                              SELECTED_LOAD_TEST_DESCRIPTOR="presigned-url-stress-test.json random-guids"
                              ;;
                          drs-endpoint)
                              echo "Selected drs-endpoint"
                              # FOR INDEXD DRDS ENDPOINTS
                              sed -i 's/"indexd_record_acl": "phs000178",/"indexd_record_acl": "$PRESIGNED_URL_ACL_FILTER",/' load-testing/sample-descriptors/load-test-drs-endpoint-bottleneck-sample.json
                              sed -i 's/"presigned_url_protocol": "phs000178",/"indexd_record_acl": "SIGNED_URL_PROTOCOL",/' load-testing/sample-descriptors/load-test-drs-endpoint-bottleneck-sample.json
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-drs-endpoint-bottleneck-sample.json random-guids"
                              ;;
                          ga4gh-drs-performance)
                              echo "Selected drs-performance"
                              # FOR DRS ENDPOINTS
                              # use ; as sed delimeter
                              sed -i 's;"indexd_record_authz_list": "/programs/DEV/projects/test1,/programs/DEV/projects/test2,/programs/DEV/projects/test3",;"indexd_record_authz_list": "$PRESIGNED_URL_AUTHZ_FILTER",;' load-testing/sample-descriptors/load-test-ga4gh-drs-performance-sample.json

                              sed -i 's/"presigned_url_protocol": "s3",/"presigned_url_protocol": "$SIGNED_URL_PROTOCOL",/' load-testing/sample-descriptors/load-test-ga4gh-drs-performance-sample.json
                              sed -i 's/"minimum_records": 10000,/"minimum_records": "$MINIMUM_RECORDS",/' load-testing/sample-descriptors/load-test-ga4gh-drs-performance-sample.json
                              sed -i 's/"record_chunk_size": 1024,/"record_chunk_size": "$RECORD_CHUNK_SIZE",/' load-testing/sample-descriptors/load-test-ga4gh-drs-performance-sample.json
                              sed -i 's/"num_parallel_requests": 5,/"num_parallel_requests": "$NUM_PARALLEL_REQUESTS",/' load-testing/sample-descriptors/load-test-ga4gh-drs-performance-sample.json
                              sed -i 's/"passports_list": "",/"passports_list": "$PASSPORTS_LIST",/' load-testing/sample-descriptors/load-test-ga4gh-drs-performance-sample.json

                              sed -i 's/"MTLS_DOMAIN": "qa-dcp.planx-pla.net",/"MTLS_DOMAIN": "'"$MTLS_DOMAIN"'",/' load-testing/sample-descriptors/load-test-ga4gh-drs-performance-sample.json

                              # use ; as sed delimeter
                              sed -i 's;"MTLS_CERT": "mtls.crt",;"MTLS_CERT": "'"$JENKINS_PATH\\/mtls.crt"'",;' load-testing/sample-descriptors/load-test-ga4gh-drs-performance-sample.json
                              sed -i 's;"MTLS_KEY": "mtls.key";"MTLS_KEY": "'"$JENKINS_PATH\\/mtls.key"'";' load-testing/sample-descriptors/load-test-ga4gh-drs-performance-sample.json

                              echo "\nload-test-ga4gh-drs-performance-sample.json contents:"
                              cat load-testing/sample-descriptors/load-test-ga4gh-drs-performance-sample.json
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-ga4gh-drs-performance-sample.json"
                              ;;
                          sheepdog-import-clinical-metada)
                              echo "Selected Sheepdog import clinical metadata"
                              # FOR SHEEPDOG IMPORT
                              sed -i 's/"num_of_records": 1000,/"num_of_records": $SHEEPDOG_NUM_OF_RECORDS_TO_IMPORT,/' load-testing/sample-descriptors/load-test-sheepdog-import-clinical-metadata.json
                              sed -i 's/"override_access_token": "<place_access_token_here>",/"override_access_token": "$ACCESS_TOKEN",/' load-testing/sample-descriptors/load-test-sheepdog-import-clinical-metadata.json
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-sheepdog-import-clinical-metadata.json"
                              ;;
                          create-indexd-records)
                              echo "Selected create indexd records"
                              # FOR INDEXD RECORDS CREATION
                              mv "$ED_DEV_ENV_CREDS_JSON" credentials.json
                              sed -i 's/"num_of_records": 1000,/"num_of_records": $INDEXD_NUM_OF_RECORDS_TO_CREATE,/' load-testing/sample-descriptors/load-test-create-indexd-records.json
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-create-indexd-records.json"
                              ;;
                          metadata-service-create-and-query)
                              echo "Selected Metadata Service create and query test"
                              # FOR MDS create and query
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-metadata-service-create-and-query-sample.json"
                              ;;
                          metadata-service-filter-large-database)
                              echo "Selected Metadata Service filter large database test"
                              # FOR MDS soak test
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-metadata-service-large-database-sample.json"
                              ;;
                          metadata-service-create-and-delete)
                              echo "Selected Metadata Service filter large database test"
                              # FOR MDS soak test
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-metadata-service-create-and-delete-sample.json"
                              ;;
                          metadata-service-create-mds-record)
                              echo "Selected Metadata Service filter large database test"
                              # FOR MDS soak test
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-metadata-service-create-mds-sample.json"
                              ;;
                          study-viewer)
                              echo "Selected Study Viewer test"
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-study-viewer.json"
                              sed -i 's/"override_access_token": "<place_access_token_here>",/"override_access_token": "$QA_NIAID_CREDS",/' load-testing/sample-descriptors/load-test-study-viewer.json
                              ;;
                          study-viewer)
                              echo "Selected Study Viewer test"
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-study-viewer.json"
                              sed -i 's/"override_access_token": "<place_access_token_here>",/"override_access_token": "$QA_NIAID_CREDS",/' load-testing/sample-descriptors/load-test-study-viewer.json
                              ;;
                          audit-presigned-url)
                              echo "Selected Audit Service Presigned URL test"
                              mv "$QA_NIAID_CREDS" credentials.json
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-audit-presigned-urls-sample.json"
                              ;;
                          audit-login)
                              echo "Selected Audit Service Login test"
                              mv "$QA_NIAID_CREDS" credentials.json
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-audit-login-sample.json"
                              ;;
                          esac

                          node load-testing/loadTestRunner.js credentials.json load-testing/sample-descriptors/\$SELECTED_LOAD_TEST_DESCRIPTOR

                          echo "done"
                        """
                        }
                    }
                }
            }
        }
        stage('upload results') {
            steps {
                script {
                    sh """#!/bin/bash -x

                        echo "uploading results..."
                        aws s3 cp ./gen3-qa/result.json "s3://qaplanetv1-data-bucket/\$RELEASE_VERSION/\$LOAD_TEST_DESCRIPTOR/result_\$(date +%s).json"

                        # if the TEST_DESCRIPTOR is AUDIT-SERVICE-*, add the result to specific location
                        # but the location is TBD
                    """
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'gen3-qa/result.json'
        }
    }
}
