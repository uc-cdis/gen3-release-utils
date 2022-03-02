/*
  String parameter TARGET_ENVIRONMENT
    e.g., qa-heal
  String parameter JOB_NAME
    e.g., metadata-aggregate-sync
*/
pipeline {
  agent {
    node {
      label 'gen3-qa-worker'
    }
  }
  stages {
      stage('Clean old workspace') {
          steps {
              cleanWs()
          }
      }
      stage('Checkout code') {
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
      stage('Invoke gen3 job') {
      steps {
        dir("run-gen3-job") {
          sh '''#!/bin/bash +x
            set -e
            export GEN3_HOME=\$WORKSPACE/cloud-automation
            export KUBECTL_NAMESPACE=\${TARGET_ENVIRONMENT}
            source $GEN3_HOME/gen3/gen3setup.sh
            gen3 kube-setup-secrets
            if [ $GEN3_ROLL_ALL == "true" ]; then
              gen3 roll all
            fi
            gen3 job run \${JOB_NAME}
            sleep 60
            gen3 job logs \${JOB_NAME} -f
            echo "done"
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
