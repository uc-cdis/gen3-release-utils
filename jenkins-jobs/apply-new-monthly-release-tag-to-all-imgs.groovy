/*
  String parameter RELEASE_VERSION
    e.g., 2021.04
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
                // gen3-release-utils
                checkout([
                  $class: 'GitSCM',
                  branches: [[name: 'refs/heads/master']],
                  doGenerateSubmoduleConfigurations: false,
                  extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'gen3-release-utils']],
                  submoduleCfg: [],
                  userRemoteConfigs: [[credentialsId: 'PlanXCyborgUserJenkins', url: 'https://github.com/uc-cdis/gen3-release-utils.git']]
                ])
            }
        }
        stage('Iterate through all repos, find their img names and apply new tag') {
            steps {
              dir("gen3-release-utils") {
                script {
                    println("### ## current path: ${env.WORKSPACE}");

                    sh "ls -ilh ${env.WORKSPACE}/gen3-release-utils"

                    // Read the contents of repo_list.txt
                    String fileContents = readFile "${env.WORKSPACE}/gen3-release-utils/repo_list.txt"

                    List<String> repos = Arrays.asList(LIST_OF_REPOS_WHOSE_IMAGES_NEED_TO_BE_TAGGED.split("\n"));

                    def quietPeriod = 0;
                    def jenkins = Jenkins.getInstance()
                    def job = jenkins.getItem("quay-apply-new-tag-to-img");

                    year = RELEASE_VERSION.split("\\.")[0]
                    month = RELEASE_VERSION.split("\\.")[1]
                    currentImg = "integration${year}${month}"

                    reposAndImageNames = [
                        "pelican": "pelican-export",
                        "docker-nginx": "nginx",
                        "gen3-fuse": "gen3fuse-sidecar",
                        "cloud-automation": "awshelper",
                        "dataguids.org": "dataguids",
                    ]

                    repos.each{ githubRepoName ->
                      imgName = githubRepoName
                      if (reposAndImageNames.containsKey(githubRepoName)) {
                        imgName = reposAndImageNames[githubRepoName];
                        println "Applying new image tag ${RELEASE_VERSION} to img ${imgName}...";

                        def params = []

                        params += new StringParameterValue("SERVICE_NAME", imgName);
                        params += new StringParameterValue("CURRENT_IMG_TAG", currentImg);
                        params += new StringParameterValue("NEW_IMG_TAG", RELEASE_VERSION);

                        def paramsAction = new ParametersAction(params);
                        hudson.model.Hudson.instance.queue.schedule(job, quietPeriod, null, paramsAction);
                        quietPeriod += 1;
                      }
                      else if (githubRepoName == "sower-jobs") {
                        sowerJobsImages=['metadata-manifest-ingestion', 'get-dbgap-metadata', 'manifest-indexing', 'download-indexd-manifest']

                        sowerJobsImages.each{ sowerJobsImg ->
                          println "Applying new image tag ${RELEASE_VERSION} to img from repo ${sowerJobsImg}...";

                          def params = []

                          params += new StringParameterValue("SERVICE_NAME", imgName);
                          params += new StringParameterValue("CURRENT_IMG_TAG", currentImg);
                          params += new StringParameterValue("NEW_IMG_TAG", RELEASE_VERSION);

                          def paramsAction = new ParametersAction(params);
                          hudson.model.Hudson.instance.queue.schedule(job, quietPeriod, null, paramsAction);
                          quietPeriod += 1;
                        }
                      }
                      else if (githubRepoName == "mariner") {
                        marinerImages=['mariner-engine', 'mariner-s3sidecar', 'mariner-server']

                        marinerImages.each{ marinerImg ->
                          println "Applying new image tag ${RELEASE_VERSION} to img from repo ${marinerImg}...";

                          def params = []

                          params += new StringParameterValue("SERVICE_NAME", imgName);
                          params += new StringParameterValue("CURRENT_IMG_TAG", currentImg);
                          params += new StringParameterValue("NEW_IMG_TAG", RELEASE_VERSION);

                          def paramsAction = new ParametersAction(params);
                          hudson.model.Hudson.instance.queue.schedule(job, quietPeriod, null, paramsAction);
                          quietPeriod += 1;
                        }
                      } else {
                        println "Applying new image tag ${RELEASE_VERSION} to img ${imgName}...";

                        def params = []

                        params += new StringParameterValue("SERVICE_NAME", imgName);
                        params += new StringParameterValue("CURRENT_IMG_TAG", currentImg);
                        params += new StringParameterValue("NEW_IMG_TAG", RELEASE_VERSION);

                        def paramsAction = new ParametersAction(params);
                        hudson.model.Hudson.instance.queue.schedule(job, quietPeriod, null, paramsAction);
                        quietPeriod += 1;
                      }
                    }
                }
              }
            }
        }
    }
}
