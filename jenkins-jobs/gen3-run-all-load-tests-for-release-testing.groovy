/*
  String parameter LIST_OF_LOAD_TEST_SCENARIOS
    Default value: fence-presigned-url,sheepdog-import-clinical-metada,metadata-service-create-and-query,metadata-service-filter-large-database

  String parameter RELEASE_VERSION
    e.g., 2021.04
*/

List<String> environments = Arrays.asList(LIST_OF_LOAD_TEST_SCENARIOS.split("\\s*,\\s*"));

def quietPeriod = 0;

def jenkins = Jenkins.getInstance()

def job = jenkins.getItem("gen3-run-load-tests");

environments.each {loadTestScenario ->
  println "Running load test for ${loadTestScenario}...";

  def params = []

  params += new StringParameterValue("LOAD_TEST_DESCRIPTOR", loadTestScenario);

  params += new StringParameterValue("TARGET_ENVIRONMENT", "qa-dcp");
  params += new StringParameterValue("PRESIGNED_URL_ACL_FILTER", "QA");
  params += new StringParameterValue("SHEEPDOG_NUM_OF_RECORDS_TO_IMPORT", "100");
  params += new StringParameterValue("INDEXD_NUM_OF_RECORDS_TO_CREATE", "1000");
  params += new StringParameterValue("DESIRED_NUMBER_OF_FENCE_PODS", "10");

  params += new StringParameterValue("RELEASE_VERSION", "${RELEASE_VERSION}");

  def paramsAction = new ParametersAction(params);
  hudson.model.Hudson.instance.queue.schedule(job, quietPeriod, null, paramsAction);
  quietPeriod += 3600;
}
