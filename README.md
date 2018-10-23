About
=====

This is a basic Cisco Directory Service for the 7940/7960 phones. As used by radio ZFM Zandvoort. Written in Perl using CGI.

The script reads the user displayName and telephoneNumber from LDAP (active directory), supports vip sorting, pagination and outputs a valid XML.

Pagination is done using the `Refresh` header as documented by Cisco.

Requirements
============

The following Perl modules are required:

- Net::LDAP
- XML::LibXML
- CGI
