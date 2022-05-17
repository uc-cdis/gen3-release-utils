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
                  branches: [[name: 'refs/heads/chore/dicom_server_load_test']],
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
                sh """#!/bin/bash -e
                  export KUBECTL_NAMESPACE="${TARGET_ENVIRONMENT}"
                  # setup gen3 CLI
                  export GEN3_HOME=\$WORKSPACE/cloud-automation
                  source \$GEN3_HOME/gen3/gen3setup.sh
                  gen3 api api-key cdis.autotest@gmail.com > ./gen3-qa/credentials.json
                """
          }
        }
        stage('run tests') {
            environment {
                JENKINS_PATH = sh(script: 'pwd', , returnStdout: true).trim()
            }
            steps {
                  dir("gen3-qa") {
                      script {
                        def selectedLoadTestDescriptor = LOAD_TEST_DESCRIPTOR
                        sh """#!/bin/bash -x

                          export GEN3_HOME=../cloud-automation
                          export TEST_DATA_PATH=../testData
                          export GEN3_SKIP_PROJ_SETUP=true
                          export RUNNING_LOCAL=false
                          export K6_STATSD_ADDR=\$DD_AGENT_HOST:8125
                          export K6_STATSD_ENABLE_TAGS=true
                          export USE_DATADOG=true


                          npm install

                          SELECTED_LOAD_TEST_DESCRIPTOR=""

                          # TODO: Make this work
                          # case statement to use one of the load test descriptor JSON files
                          case $selectedLoadTestDescriptor in
                          dicom-server-metadata)
                              echo "Selected Dicom Server Metadata test"
                              export KUBECTL_NAMESPACE="${TARGET_ENVIRONMENT}"
                              export GEN3_HOME=\$WORKSPACE/cloud-automation
                              source \$GEN3_HOME/gen3/gen3setup.sh
                              gen3 api api-key cdis.autotest@gmail.com > credentials.json
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-dicom-server-metadata.json"
                              ;;
                          dicom-viewer-study)
                              echo "Selected Dicom Viewer Study test"
                              export KUBECTL_NAMESPACE="${TARGET_ENVIRONMENT}"
                              export GEN3_HOME=\$WORKSPACE/cloud-automation
                              source \$GEN3_HOME/gen3/gen3setup.sh
                              gen3 api api-key cdis.autotest@gmail.com > credentials.json
                              SELECTED_LOAD_TEST_DESCRIPTOR="load-test-dicom-viewer-study.json"
                              ;;
                          esac
                          cat credentials.json
                          node load-testing/loadTestRunnerV2.js credentials.json load-testing/sample-descriptors/\$SELECTED_LOAD_TEST_DESCRIPTOR

                          echo "done"
                        """
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
            archiveArtifacts artifacts: 'gen3-qa/result.json, gen3-qa/screenshots/*.png'
        }
    }
}
