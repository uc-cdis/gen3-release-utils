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
                // gen3-release-utils
                checkout([
                  $class: 'GitSCM',
                  branches: [[name: 'refs/heads/chore/run_datadog_container_in_load_tests']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'gen3-release-utils']],
                  submoduleCfg: [],
                  userRemoteConfigs: [[credentialsId: 'PlanXCyborgUser', url: 'https://github.com/uc-cdis/gen3-release-utils.git']]
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
                  file(credentialsId: 'CTDS_TEST_ENV_CREDS_JSON', variable: 'CTDS_TEST_ENV_CREDS_JSON'),
                  string(credentialsId: 'DD_API_KEY', variable: 'DD_API_KEY')
                ]){
                  dir("gen3-qa") {
                      script {
                        def selectedLoadTestDescriptor = LOAD_TEST_DESCRIPTOR
                        sh """#!/bin/bash -x

                          export GEN3_HOME=../cloud-automation
                          export TEST_DATA_PATH=../testData
                          export GEN3_SKIP_PROJ_SETUP=true
                          export RUNNING_LOCAL=false
                          export USE_DATADOG=true
                          export K6_STATSD_ADDR=172.24.223.188:8125

                          DOCKER_CONTENT_TRUST=1 \
                          docker run -d \
                              --name datadog \
                              -v /var/run/docker.sock:/var/run/docker.sock:ro \
                              -v /proc/:/host/proc/:ro \
                              -v /sys/fs/cgroup/:/host/sys/fs/cgroup:ro \
                              -e DD_SITE="datadoghq.com" \
                              -e DD_API_KEY="$DD_API_KEY" \
                              -e DD_DOGSTATSD_NON_LOCAL_TRAFFIC=1 \
                              -p 8125:8125/udp \
                              datadog/agent:latest

                          mv "$QA_DCP_CREDS_JSON" credentials.json

                          SELECTED_LOAD_TEST_DESCRIPTOR=""

                          # node load-testing/loadTestRunner.js credentials.json load-testing/sample-descriptors/\$SELECTED_LOAD_TEST_DESCRIPTOR
                          K6_STATSD_ENABLE_TAGS=true k6 run --out statsd --duration 30s $JENKINS_PATH/gen3-release-utils/jenkins-jobs/dummy-load-test-script.js
                          echo "done"
                          docker rm -f datadog
                        """
                        }
                    }
                }
            }
        }
    }
}
