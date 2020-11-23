require 'time'
require 'date'
require 'net/http'
require 'openssl'
require 'uri'
require 'cgi'
require 'json'

def httpGetter(url_str)
  url = URI.parse(url_str)
  http = Net::HTTP.new(url.host, url.port)
  request = Net::HTTP::Get.new(url.request_uri)
  request['Authorization'] = "token #{ENV['GITHUB_TOKEN'].chomp}"
  http.use_ssl = true
  response = http.request(request)
  j = JSON[response.body]
end

server = "https://api.github.com"
repo = "cdis-manifest"

listOfClosedPRs = httpGetter("#{server}/repos/uc-cdis/#{repo}/pulls\?state\=closed")

stats = Hash.new({ value: 0 })

total_prs = 0
total_failures = 0
force_merges = Array.new

listOfClosedPRs.each { |pr|
  puts("#{pr['number']} - #{pr['updated_at']}")
  updated_at = Time.parse(pr['updated_at'])
  # only PRs from the last 168hs (1 week)
  puts("updated_at: #{updated_at}")
  puts("168hs ago: #{Time.now - (3600 * 168)}")
  if updated_at >= Time.now - (3600 * 168)
    total_prs = total_prs + 1
    prMetadata = httpGetter("#{server}/repos/uc-cdis/#{repo}/pulls/#{pr['number']}")
    prStatuses = httpGetter("#{prMetadata['statuses_url']}")
    puts("state: #{prStatuses[0]['state']}")
    if prStatuses[0]['state'] != 'success'
      total_failures = total_failures + 1
      if prMetadata['merged']
        force_merges.append("PR ##{pr['number']} -> Merged by: #{prMetadata['user']['login']}")
      end
    end
  end
}

stats['num_of_prs'] = { label: 'num of PRs', value: "#{total_prs}" }
stats['num_of_failures'] = { label: 'total failures', value: "#{total_failures}" }
stats['force_merges'] = { label: 'force merges', value: "#{force_merges}" }

# puts JSON.pretty_generate(stats)

qabot_msg = "oh nous :oof: looks like we have some force-merges in `cdis-manifest`..."
qabot_msg += '```'
force_merges.each { |fm|
  qabot_msg += fm + "\n"
}
qabot_msg += '```'

uri = URI.parse("https://slack.com/api/chat.postMessage?token=#{ENV['QABOT_SLACK_API_TOKEN'].chomp}&channel=CPG3R0R9Q&icon_url=https://avatars.slack-edge.com/2019-11-23/846894374304_3adeb13422453e142051_192.png&username=qa-bot&text=#{CGI.escape(qabot_msg)}")
header = {'Content-Type': 'text/json'}

# Create the HTTP objects
http = Net::HTTP.new(uri.host, uri.port)
request = Net::HTTP::Post.new(uri.request_uri, header)
http.use_ssl = true

# Send the request
response = http.request(request)
puts response
