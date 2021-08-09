/*
  This job sends a slack bot message to call another bot (for transparency / visibility on what is being replayed).

  String parameter PRS_TO_BE_REPLAYED
    Format: comma-separated list of [<repo_name><whitespace><pr_number>] values
    Example: e.g., cdis-manifest PR-3216,cdis-manifest PR-3176,gitops-qa PR-1506,cdis-manifest PR-3215,data-portal PR-876,hatchery PR-14,data-portal PR-876,data-portal PR-887,cloud-automation PR-1663,gen3-qa PR-647,cdis-jenkins-lib PR-196,cdis-manifest PR-3214,cdis-manifest PR-3213
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
        stage('Replay a bunch of PRs') {
            steps {
              withCredentials([
                string(credentialsId: 'SDET_BOT_SLACK_API_TOKEN', variable: 'SDET_BOT_SLACK_API_TOKEN')
              ]){
                script {
                    List<String> prsToBeReplayed = Arrays.asList(PRS_TO_BE_REPLAYED.split("\\s*,\\s*"));

                    prsToBeReplayed.each {pr ->
                        def repo = pr.split(" ")[0];
                        def prNum = pr.split(" ")[1];
                        println "Replaying PR ${prNum} from ${repo}...";

                        sh """#!/bin/bash +x
                            export GEN3_HOME=\$WORKSPACE/cloud-automation

                            curl -X POST "https://cdis.slack.com/api/chat.postMessage?token=\$SDET_BOT_SLACK_API_TOKEN&channel=${CHANNEL_ID}&icon_url=https://avatars.slack-edge.com/2020-08-09/1303194126929_463d1342f0b003d50ec8_48.jpg&username=replay-bot&text=<@${QABOT_ID}>%20replay-pr%20${repo}%20${prNum}"
                            echo "replayed!"

                            sleep 1200
                        """

                        println('debugging ' + pr)
                    }
                  }
                }
            }
        }
    }
}
