pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: shell
    image: quay.io/cdis/jenkins:master
    command:
    - sleep
    args:
    - infinity
    env:
    - name: AWS_DEFAULT_REGION
      value: us-east-1
    - name: JAVA_OPTS
      value: "-Xmx3072m"
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
'''
            defaultContainer 'shell'
        }
    }
    stages {
        stage('Clean Workspace') {
          steps {
            cleanWs()
          }
        }
        stage('Fetch Code') {
            steps {
                // gen3sdk-python
                checkout([
                  $class: 'GitSCM',
                  branches: [[name: 'refs/heads/master']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'gen3sdk-python']],
                  submoduleCfg: [],
                  userRemoteConfigs: [[credentialsId: 'PlanXCyborgUserJenkins', url: 'https://github.com/uc-cdis/cloud-automation.git']]
                ])
                // gen3-qa
                checkout([
                  $class: 'GitSCM',
                  branches: [[name: 'refs/heads/master']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'gen3-qa']],
                  submoduleCfg: [],
                  userRemoteConfigs: [[credentialsId: 'PlanXCyborgUserJenkins2', url: 'https://github.com/uc-cdis/gen3sdk-python.git']]
                ])
            }
        }
        stage('Download manifest and move it to work folder') {
            steps {
                dir("gen3sdk-python") {
                    sh 'echo "downloading ${MANIFEST_FILE}..."'
                    sh 'aws s3 cp s3://${S3_BUCKET}/${MANIFEST_FILE} .'
                    sh 'mkdir work'
                    sh 'mv ${MANIFEST_FILE} work/'
                }
            }
        }
        stage('copy manifest utils CLI script') {
            steps {
                dir("gen3sdk-python") {
                    sh 'cp ../gen3-qa/scripts/data-manifest-qa-cli.py .'
                }
            }
        }
        stage('Start the manifest QA process') {
            steps {
                dir("gen3sdk-python") {
                    sh '''#!/bin/bash -x
                        which python
                        which python3

                        # TODO: Install poetry in a proper docker image instead of doing it here
                        curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 -
                        source $HOME/.poetry/env
                        echo "QAing ${MANIFEST_FILE}"
                        # For debugging purposes
                        # sleep 3000
                       poetry install -vv --no-dev
                       poetry run python3 data-manifest-qa-cli.py checkindex -m work/${MANIFEST_FILE} -e ${TARGET_GEN3_COMMONS}
                      '''
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: '**/*.log'
            // cleanWs()
        }
    }
}
