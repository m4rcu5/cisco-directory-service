#!/usr/bin/perl
use strict;
use warnings;
use CGI qw(:standard);
use POSIX;
use Net::LDAP;
use XML::LibXML;

# Configuration parameters
# -----------------------

# Bind details for LDAP server
my $ldapHost   = 'zfm.lan';
my $ldapBindDN = 'cn=asterisk,ou=Service Accounts,ou=Tolweg,dc=zfm,dc=lan';
my $ldapPasswd = 'geheim';

# Search base and filter
my $ldapBaseDN = 'ou=User Accounts,ou=Tolweg,dc=zfm,dc=lan';
my $ldapFilter = '(&(objectClass=person)(telephoneNumber=*))';

# The regex which will move these users to the top
# of the directory (aka vip). Comment to disable
my $vipRegex = qr/^ZFM/x;


# CGI initialization
# ------------------
my $q = CGI->new;

# Retrieve page param
my $page = $q->param('page') // 1;


# Data retrieval
# --------------

# LDAP connection
my $ldap = Net::LDAP->new( $ldapHost );

# Bind to directory with DN and password
my $mesg = $ldap->bind( $ldapBindDN, password => $ldapPasswd );

# Find all users with phones numbers
$mesg = $ldap->search(
    base   => $ldapBaseDN,
    filter => $ldapFilter
);

# Die if ldap throws an error
if ($mesg->code) {
    die $mesg->error, "\n";
}

my (@userList, @vipUserList);

# Retrieve the users from LDAP
foreach my $entry ($mesg->entries) {
    my $displayName     = $entry->get_value('displayName');
    my $telephoneNumber = $entry->get_value('telephoneNumber');

    # Check if the user matches the VIP regex (if enabled)
    if (defined($vipRegex) && $displayName =~ $vipRegex) {
        push(@vipUserList, {
            displayName     => $displayName,
            telephoneNumber => $telephoneNumber
        });
    } else {
        push(@userList, {
            displayName     => $displayName,
            telephoneNumber => $telephoneNumber
        });
    }
}

# Sort the 2 lists by DisplayName
@userList    = sort { $a->{displayName} cmp $b->{displayName} } @userList;
@vipUserList = sort { $a->{displayName} cmp $b->{displayName} } @vipUserList;

# Combine the 2 lists into one
unshift(@userList, @vipUserList);


# Print header
# ------------
my $next_page = 1;

# Fit 32 entries on a page, if we have more there is a next
if ($page < ceil( $#userList / 32)) {
    $next_page++;
}

# The 'Next' softkey triggers a reload, looking at the refresh header
# this is the Cisco way of accessing the next page of the directory
print $q->header(
    -Type    => 'text/xml',
    -Expires => '-1',
    -Refresh => '0; url=' . $q->url . '?page=' . $next_page
);


# Data output to browser
# ----------------------
my ($doc, $root, $title, $prompt);

# Document root
$doc = XML::LibXML::Document->new('1.0', 'utf-8');
$root = $doc->createElement('CiscoIPPhoneDirectory');

# Title
$title = $root->addNewChild(undef, 'Title');
$title -> appendTextNode('Central directory');

# Prompt
$prompt = $root->addNewChild(undef, 'Prompt');
$prompt -> appendTextNode(
    'Page ' . $page . ' of ' . ceil( $#userList / 32 )
);

# Start of this page
my $count = ($page * 32) - 32;

# Loop over entries until we reached the page max of 32
while ( $count <= ($page * 32) && $count <= $#userList ){
    my ($entry, $name, $tel);

    my $user = $userList[$count];

    $entry = $doc->createElement('DirectoryEntry');

    $name  = $entry->addNewChild(undef, 'Name');
    $name  -> appendTextNode($user->{displayName});
    $tel   = $entry->addNewChild(undef, 'Telephone');
    $tel   -> appendTextNode($user->{telephoneNumber});

    $root -> appendChild($entry);

    $count++
}

# Build document
$doc->setDocumentElement($root);

# Print to browser
print $doc->toString(2);
