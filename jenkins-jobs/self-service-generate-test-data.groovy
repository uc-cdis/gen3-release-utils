/*
  Choice parameter TARGET_ENVIRONMENT
    Values: qa-anvil
            qa-dcp
            qa-brain
            qa-ibd
            qa-mickey
            qa-heal

  String parameter TEST_PROGRAM
    Default value: jnkns

  String parameter TEST_PROJECT
    Default value: jenkins2
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
                // data-simulator
                checkout([
                  $class: 'GitSCM',
                  branches: [[name: 'refs/heads/master']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'data-simulator']],
                  submoduleCfg: [],
                  userRemoteConfigs: [[credentialsId: 'PlanXCyborgUser', url: 'https://github.com/uc-cdis/data-simulator.git']]
                ])
            }
        }
        stage('Invoke gentestdata gen3 job') {
            steps {
                dir("generate-test-data") {
                    sh '''#!/bin/bash +x
                        export GEN3_HOME=\$WORKSPACE/cloud-automation
                        export KUBECTL_NAMESPACE=\${TARGET_ENVIRONMENT}

                        source $GEN3_HOME/gen3/gen3setup.sh

                        gen3 job run gentestdata SUBMISSION_USER cdis.autotest@gmail.com TEST_PROGRAM $TEST_PROGRAM TEST_PROJECT $TEST_PROJECT

                        sleep 40

                        gen3 job logs gentestdata -f

                        echo "done"
                    '''
                }
            }
        }
    }
}
