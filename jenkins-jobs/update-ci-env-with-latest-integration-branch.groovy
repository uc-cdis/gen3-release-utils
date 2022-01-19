/*
  String parameter INTEGRATION_BRANCH
    Default value: integration202109
  String parameter PR_TITLE
    Default value: Updating CI env with
  String parameter TARGET_ENVIRONMENT
    format: qa-dcp.planx-pla.net
  String parameter REPO_NAME
    format: gitops-qa
*/


pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: gen3-qa-worker
    netnolimit: "yes"
spec:
  containers:
  - name: shell
    image: quay.io/cdis/gen3-qa-worker:master
    imagePullPolicy: Always
    command:
    - sleep
    args:
    - infinity
    env:
    - name: http_proxy
      value: "http://cloud-proxy.internal.io:3128"
    - name: https_proxy
      value: "http://cloud-proxy.internal.io:3128"
    - name: no_proxy
      value: "localhost,127.0.0.1,localaddress,169.254.169.254,.internal.io,logs.us-east-1.amazonaws.com"
    - name: AWS_DEFAULT_REGION
      value: us-east-1
    - name: AWS_ACCESS_KEY_ID
      valueFrom:
        secretKeyRef:
          name: jenkins-secret
          key: aws_access_key_id
    - name: AWS_SECRET_ACCESS_KEY
      valueFrom:
        secretKeyRef:
          name: jenkins-secret
          key: aws_secret_access_key
  serviceAccount: gen3-self-service-account
  serviceAccountName: gen3-self-service-account
'''
            defaultContainer 'shell'
        }
    }
    stages {
        stage('Clean up') {
            steps {
                cleanWs()
            }
        }
        stage('Initial setup') {
            steps {
                // manifest repo
                checkout([
                  $class: 'GitSCM',
                  branches: [[name: 'refs/heads/master']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: "${REPO_NAME}"]],
                  submoduleCfg: [],
                  userRemoteConfigs: [[credentialsId: 'PlanXCyborgUser', url: "https://github.com/uc-cdis/${REPO_NAME}"]]
                ])
                // gen3-release-utils
                checkout([
                  $class: 'GitSCM',
                  branches: [[name: '*/master']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'gen3-release-utils']],
                  submoduleCfg: [],
                  userRemoteConfigs: [[credentialsId: 'PlanXCyborgUser', url: 'https://github.com/uc-cdis/gen3-release-utils']]
                ])
            }
        }
        stage('Update CI environment') {
            steps {
              withCredentials([usernamePassword(credentialsId: 'PlanXCyborgUser', usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GITHUB_TOKEN')]) {
                dir("gen3-release-utils/gen3release-sdk") {
                    sh '''
                      export PATH=$PATH:/home/jenkins/.local/bin:/home/jenkins/.local/lib
                      pip3 install -U pip --user
                      poetry install
                      poetry run gen3release apply -v $INTEGRATION_BRANCH -e ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT} -pr "${PR_TITLE} ${INTEGRATION_BRANCH} ${TARGET_ENVIRONMENT} $(date +%s) -l gen3-release"
                    '''
                }
              }
            }
        }
    }
}
