ipipeline {
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
                  userRemoteConfigs: [[credentialsId: 'PlanXCyborgUserJenkins2', url: 'https://github.com/uc-cdis/cloud-automation.git']]
                ])
            }
        }
        stage('Gen3 Roll') {
            steps {
                sh '''#!/bin/bash +x
                    export GEN3_HOME=\$WORKSPACE/cloud-automation
                    export KUBECTL_NAMESPACE="default"

                    source $GEN3_HOME/gen3/gen3setup.sh

                    SELENIUM_HUB_POD_NAME=\$(g3kubectl get pods | grep selenium-hub | awk '{ print \$1 }')
                    echo "Found selenium-hub pod name: \${SELENIUM_HUB_POD_NAME}"
                    g3kubectl exec -i \${SELENIUM_HUB_POD_NAME} -c hub -- curl http://localhost:4444/status | jq .value.message > selenium-status.txt

                    echo "done"
                '''

            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: '*.txt'
        }
    }
}
