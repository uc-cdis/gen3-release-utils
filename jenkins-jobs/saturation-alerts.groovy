// schedule: H 11 * * *
pipeline {
    agent {
      node {
        label 'master'
      }
    }
    stages {
        stage('Clean old workspace') {
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
                  userRemoteConfigs: [[credentialsId: 'PlanXCyborgUserJenkins', url: 'https://github.com/uc-cdis/cloud-automation.git']]
                ])
            }
        }
        stage('Check resources') {
            steps {
                sh '''#!/bin/bash +x

                    # setup gen3 CLI
                    export GEN3_HOME=\$WORKSPACE/cloud-automation
                    source  \$GEN3_HOME/gen3/lib/utils.sh
                    source \$GEN3_HOME/gen3/gen3setup.sh

                    disk_usage_master=\$(df -h | grep jenkins_home | awk '{ print \$5 }')
                    echo "disk_usage_master: \$disk_usage_master"
                    disk_usage_master_number_only=\$(echo \$disk_usage_master | sed 's/%//')

                    if [ \$disk_usage_master_number_only -gt 80 ]; then
                        echo "All PR checks wil crash soon unless some disk space is cleared";
                        curl -X POST --data-urlencode "payload={\\\"channel\\\": \\\"#gen3-qa-notifications\\\", \\\"username\\\": \\\"qa-bot\\\", \\\"text\\\": \\\"Jenkins is running out of disk space (current disk space usage \$disk_usage_master_number_only%). IF we do not clear some disk space, all PR checks will fail :red_circle:\\\", \\\"icon_emoji\\\": \\\":floppy_disk:\\\"}" \$(g3kubectl get configmap global -o jsonpath={.data.jenkins_saturation_notifications_webhook})
                    else
                        curl -X POST --data-urlencode "payload={\\\"channel\\\": \\\"#gen3-qa-notifications\\\", \\\"username\\\": \\\"qa-bot\\\", \\\"text\\\": \\\"all good with Jenkins... :white_check_mark: (current disk space usage \$disk_usage_master_number_only%) \\\", \\\"icon_emoji\\\": \\\":floppy_disk:\\\"}" \$(g3kubectl get configmap global -o jsonpath={.data.jenkins_saturation_notifications_webhook})
                        echo "all good"
                    fi

                    disk_usage_ci_worker=\$(g3kubectl exec -it \$(gen3 pod jenkins-ci-worker) -c jenkins-worker -- df -h | grep jenkins | awk '{ print \$5 }')
                    echo "disk_usage_ci_worker: \$disk_usage_ci_worker"
                    disk_usage_ci_worker_number_only=\$(echo \$disk_usage_ci_worker | sed 's/%//')

                    if [ \$disk_usage_ci_worker_number_only -gt 80 ]; then
                        echo "All PR checks wil crash soon unless some disk space is cleared";
                        curl -X POST --data-urlencode "payload={\\\"channel\\\": \\\"#gen3-qa-notifications\\\", \\\"username\\\": \\\"qa-bot\\\", \\\"text\\\": \\\"Jenkins CI Worker is running out of disk space (current disk space usage \$disk_usage_ci_worker_number_only%). IF we do not clear some disk space, all PR checks will fail :red_circle:\\\", \\\"icon_emoji\\\": \\\":floppy_disk:\\\"}" \$(g3kubectl get configmap global -o jsonpath={.data.jenkins_saturation_notifications_webhook})
                    else
                        curl -X POST --data-urlencode "payload={\\\"channel\\\": \\\"#gen3-qa-notifications\\\", \\\"username\\\": \\\"qa-bot\\\", \\\"text\\\": \\\"all good with Jenkins CI Worker... :white_check_mark: (current disk space usage \$disk_usage_ci_worker_number_only%) \\\", \\\"icon_emoji\\\": \\\":floppy_disk:\\\"}" \$(g3kubectl get configmap global -o jsonpath={.data.jenkins_saturation_notifications_webhook})
                        echo "all good"
                    fi

                    echo "done"
                '''
            }
        }
    }
}
