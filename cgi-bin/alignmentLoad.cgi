#!/usr/bin/perl -w
use strict;
use CGI qw(:standard);
use CGI::Carp qw ( fatalsToBrowser ); 
use JSON::XS; #JSON::XS is recommended to be installed for handling JSON string of big size 
use DBI;
use lib "lib/";
use lib "lib/pangu";
use pangu;
use user;
use userConfig;
use userCookie;

my $userCookie = new userCookie;
my $userId = (cookie('cid')) ? $userCookie->checkCookie(cookie('cid')) : 0;
exit if (!$userId);

my $user = new user;
my $userDetail = $user->getAllFieldsWithUserId($userId);
my $userName = $userDetail->{"userName"};

my $commoncfg = readConfig("main.conf");
my $dbh=DBI->connect("DBI:mysql:$commoncfg->{DATABASE}:$commoncfg->{DBHOST}",$commoncfg->{USERNAME},$commoncfg->{PASSWORD});

my $queryGenomeId = param ('queryGenomeId') || '';
my $subjectGenomeId = param ('subjectGenomeId') || '';
my $alignEngine = param ('alignEngine') || 'blastn';
my $alignmentFile = upload ('alignmentFile');
my $alignmentFilePath = param ('alignmentFilePath') || '';
my $alignmentInfile = "$commoncfg->{TMPDIR}/$$.tabular";

print header;

if($queryGenomeId && $subjectGenomeId && ($alignmentFile || $alignmentFilePath))
{
	my $pid = fork();
	if ($pid) {
		print <<END;
<script>
	parent.closeDialog();
	parent.errorPop("It's being loaded! This processing might take a while.");
</script>	
END
	}
	elsif($pid == 0){
		if($alignmentFilePath)
		{
			#$alignmentInfile = $alignmentFilePath;
			`cp $alignmentFilePath $alignmentInfile`;
		}
		else
		{
			open (FILE, ">$alignmentInfile");
			while (read ($alignmentFile, my $Buffer, 1024)) {
				print FILE $Buffer;
			}
			close FILE;
		}		
		`perl -p -i -e 's/\r/\n/g' $alignmentInfile`; #convert CR line terminators (MAC OS) into LF line terminators (Unix)
		close (STDOUT);
		#connect to the mysql server
		my $dbh=DBI->connect("DBI:mysql:$commoncfg->{DATABASE}:$commoncfg->{DBHOST}",$commoncfg->{USERNAME},$commoncfg->{PASSWORD});

		my $queryId;
		my $queryGenome=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
		$queryGenome->execute($queryGenomeId);
		my @queryGenome = $queryGenome->fetchrow_array();
		if($queryGenome[1] eq 'library')
		{
			my $getClones = $dbh->prepare("SELECT * FROM clones WHERE sequenced > 0 AND libraryId = ?");
			$getClones->execute($assembly[4]);
			while(my @getClones = $getClones->fetchrow_array())
			{
				my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o < 50 AND name LIKE ?");
				$getSequences->execute($getClones[1]);
				while(my @getSequences = $getSequences->fetchrow_array())
				{
					$queryId->{$getSequences[2]} = $getSequences[0];
				}
			}
		}
		if($queryGenome[1] eq 'genome')
		{
			my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o = 99 AND x = ?");
			$getSequences->execute($assembly[4]);
			while(my @getSequences = $getSequences->fetchrow_array())
			{
				$queryId->{$getSequences[2]} = $getSequences[0];
			}
		}

		my $subjectId;
		if ($queryGenomeId eq $subjectGenomeId)
		{
			$subjectId = $queryId;
		}
		else
		{
			my $subjectGenome=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$subjectGenome->execute($subjectGenomeId);
			my @subjectGenome = $subjectGenome->fetchrow_array();
			if($subjectGenome[1] eq 'library')
			{
				my $getClones = $dbh->prepare("SELECT * FROM clones WHERE sequenced > 0 AND libraryId = ?");
				$getClones->execute($assembly[4]);
				while(my @getClones = $getClones->fetchrow_array())
				{
					my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o < 50 AND name LIKE ?");
					$getSequences->execute($getClones[1]);
					while(my @getSequences = $getSequences->fetchrow_array())
					{
						$subjectId->{$getSequences[2]} = $getSequences[0];
					}
				}
			}
			if($subjectGenome[1] eq 'genome')
			{
				my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o = 99 AND x = ?");
				$getSequences->execute($assembly[4]);
				while(my @getSequences = $getSequences->fetchrow_array())
				{
					$subjectId->{$getSequences[2]} = $getSequences[0];
				}
			}
		}

		open(ALN, "$alignmentInfile") or die "cannot open file $alignmentInfile";
		while(<ALN>)
		{
			/^#/ and next;
			my @hit = split("\t",$_);
			if (exists $queryId->{$hit[0]} && exists $subjectId->{$hit[1]})
			{
				$hit[0] = $queryId->{$hit[0]};
				$hit[1] = $subjectId->{$hit[1]};
				my $insertAlignment=$dbh->prepare("INSERT INTO alignment VALUES ('', '$alignEngine', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)");
				$insertAlignment->execute(@hit);
			}
			else
			{
				next;
			}
		}
		close(ALN);
		unlink ($alignmentInfile);
		my $updateAssemblyToWork=$dbh->do("UPDATE matrix SET barcode = '1' WHERE id = $assemblyId");
	}
	else{
		die "couldn't fork: $!\n";
	} 
}
else
{
	print <<END;
<script>
	parent.errorPop("Please provide required infomation or file!");
</script>	
END
}