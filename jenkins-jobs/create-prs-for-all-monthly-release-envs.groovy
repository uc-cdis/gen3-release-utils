/*
  String parameter LIST_OF_ENVIRONMENTS
    Default value: acct.bionimbus.org,caninedc.org,data.bloodpac.org,dataprep.braincommons.org,gen3.datacommons.io,gen3testing.braincommons.org,genomel.bionimbus.org,ibdgc.datacommons.io,icgc.bionimbus.org,internalstaging.theanvil.io,nci-crdc-staging.datacommons.io,staging.braincommons.org,tbi.datacommons.io,jcoin.datacommons.io,portal.occ-data.org,gen3-neuro.datacommons.io,va-testing.datacommons.io,va.datacommons.io,vpodc.org

  String parameter PR_TITLE
    Default value: Gen3 Monthly Release

  String parameter RELEASE_VERSION
    format: yyyy.mm (e.g., 2021.04)
*/

List<String> environments = Arrays.asList(LIST_OF_ENVIRONMENTS.split("\\s*,\\s*"));

def quietPeriod = 0;

def jenkins = Jenkins.getInstance()

def job = jenkins.getItem("deploy-gen3-release-to-environment");

environments.each {env ->
  println "Creating PR for ${env}...";

  def params = []

  params += new StringParameterValue("TARGET_ENVIRONMENT", env);

  params += new StringParameterValue("RELEASE_VERSION", "${RELEASE_VERSION}");
  params += new StringParameterValue("PR_TITLE", "${PR_TITLE}");
  params += new StringParameterValue("REPO_NAME", "${REPO_NAME}");

  def paramsAction = new ParametersAction(params);
  hudson.model.Hudson.instance.queue.schedule(job, quietPeriod, null, paramsAction);
  quietPeriod += 3600;
}
