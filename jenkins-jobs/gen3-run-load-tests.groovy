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
                sh """#!/bin/bash

                  export KUBECTL_NAMESPACE="$TARGET_ENVIRONMENT"
                  # setup gen3 CLI
                  export GEN3_HOME=\$WORKSPACE/cloud-automation
                  source \$GEN3_HOME/gen3/gen3setup.sh

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
                    # sleep 60
                    g3kubectl get pods | grep fence
                  else
                    echo "Presigned URL test was not selected. Skipping auto-scaling changes..."
                  fi
                """
            }
        }
        stage('run tests') {
            steps {
                withCredentials([
                        file(credentialsId: 'fence-google-app-creds-secret', variable: 'GOOGLE_APP_CREDS_JSON'),
                        file(credentialsId: 'qa-dcp-credentials-json', variable: 'QA_DCP_CREDS_JSON'),
                        file(credentialsId: 'ed-dev-environment-credentials', variable: 'ED_DEV_ENV_CREDS_JSON'),
                        string(credentialsId: 'temporary-qa-dcp-long-living-access-token', variable: 'ACCESS_TOKEN'),
                        file(credentialsId: 'QA-NIAID-CRED', variable: 'QA_NIAID_CREDS')
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
