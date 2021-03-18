/*
  Jenkins2 (Kubernetisized)

  String parameter S3_BUCKET
    e.g., cdistest-public-test-bucket

  String parameter MANIFEST_FILE
    e.g., actual-release-1-manifest.tsv

  String parameter TARGET_GEN3_COMMONS
    e.g., preprod.gen3.biodatacatalyst.nhlbi.nih.gov
*/
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
        stage('Clean workspace') {
          steps {
            cleanWs()
          }
        }
        stage('Download manifest and move it to work folder') {
            steps {
                sh 'git clone https://github.com/uc-cdis/gen3sdk-python.git'
                dir("gen3sdk-python") {
                    sh 'echo "downloading ${MANIFEST_FILE}..."'
                    sh 'aws s3 cp s3://${S3_BUCKET}/${MANIFEST_FILE} .'
                    sh 'mkdir work'
                    sh 'mv ${MANIFEST_FILE} work/'
                }
            }
        }
        stage('fetch manifest utils CLI') {
            steps {
                dir("gen3sdk-python") {
                    sh 'curl https://gist.githubusercontent.com/themarcelor/d3367472007b405485a43805cb22e831/raw/344245386e62ed18d84cda4911f51d6f08a219d0/data-manifest-qa-cli.py -o data-manifest-qa-cli.py'
                }
            }
        }
        stage('Start the manifest QA process') {
            steps {
                dir("gen3sdk-python") {
                    sh '''#!/bin/bash -x
                        curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                        source $HOME/.poetry/env
                        echo "QAing ${MANIFEST_FILE}"
                        # For debugging purposes
                        # sleep 3000
                       poetry install -vv --no-dev
                       poetry run python data-manifest-qa-cli.py checkindex -m work/${MANIFEST_FILE} -e ${TARGET_GEN3_COMMONS}
                      '''
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: '**/*.log'
        }
    }
}
