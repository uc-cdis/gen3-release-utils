/*
  String parameter RELEASE_VERSION
    e.g., 2021.04
*/

def build = Thread.currentThread().executable

println("### ## current path: ${build.workspace.toString()}");

// Read the contents of repo_list.txt
String fileContents = new File("${build.workspace.toString()}/repo_list.txt").getText('UTF-8')

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
