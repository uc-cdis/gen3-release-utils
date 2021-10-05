/*
  String parameter RELEASE_VERSION
    e.g., 2021.04
*/

// Read the contents of repo_list.txt
String fileContents = new File('repo_list.txt').getText('UTF-8')

List<String> repos = Arrays.asList(LIST_OF_REPOS_WHOSE_IMAGES_NEED_TO_BE_TAGGED.split("\n"));

def quietPeriod = 0;
def jenkins = Jenkins.getInstance()
def job = jenkins.getItem("quay-apply-new-tag-to-img");

// TODO: create string containing integration202110 based on string 2021.10
def currentImg = RELEASE_VERSION

repos.each {githubRepoName ->
  // TODO:
  // Some repo names do not match the quay img name :( we need to convert them
  def quayRepoName = ""

  if githubRepoName == "pelican" {
     quayRepoName = "pelican-export"
  }

  println "Applying new image tag ${RELEASE_VERSION} to current img ${}...";

  def params = []

  params += new StringParameterValue("LOAD_TEST_DESCRIPTOR", loadTestScenario);

  params += new StringParameterValue("TARGET_ENVIRONMENT", "qa-dcp");
  params += new StringParameterValue("PRESIGNED_URL_ACL_FILTER", "QA");

  def paramsAction = new ParametersAction(params);
  hudson.model.Hudson.instance.queue.schedule(job, quietPeriod, null, paramsAction);
  quietPeriod += 1;
}
