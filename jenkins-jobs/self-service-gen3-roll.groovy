/*
  String parameter SERVICE_NAME
    e.g., guppy
    e.g., all

  String parameter TARGET_ENVIRONMENT
    e.g., qa-anvil
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
        stage('Initial setup') {
            steps {
                // cloud-automation
                checkout([
                  $class: 'GitSCM',
                  branches: [[name: 'refs/heads/master']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'cloud-automation']],
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
                  userRemoteConfigs: [[credentialsId: 'PlanXCyborgUserJenkins', url: 'https://github.com/uc-cdis/gen3-qa.git']]
                ])
            }
        }
        stage('Gen3 Roll') {
            steps {
                dir("do-a-barrel-roll") {
                    sh '''#!/bin/bash +x
                        export GEN3_HOME=\$WORKSPACE/cloud-automation
                        export KUBECTL_NAMESPACE=\${TARGET_ENVIRONMENT}
                        # Injecting a default aws profile if not exists
                        mkdir -p ~/.aws
                        if ! grep -q '^[[]default[]]' ~/.aws/config 2>/dev/null; then
                          printf '[default]\nregion = %s\n' "${AWS_DEFAULT_REGION}" >> ~/.aws/config
                        fi                        

                        source $GEN3_HOME/gen3/gen3setup.sh

                        gen3 roll \$SERVICE_NAME

                        echo "done"
                    '''
                }
            }
        }
    }
}
