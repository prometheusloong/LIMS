#!/usr/bin/perl -w
use strict;
use CGI qw(:standard);
use CGI::Carp qw ( fatalsToBrowser ); 
use JSON; #JSON::XS is recommended to be installed for handling JSON string of big size 
use DBI;
use lib "lib/";
use lib "lib/pangu";
use pangu;
use userCookie;

my $userCookie = new userCookie;
my $userId = (cookie('cid')) ? $userCookie->checkCookie(cookie('cid')) : 0;
exit if (!$userId);

my $commoncfg = readConfig("main.conf");
my $dbh=DBI->connect("DBI:mysql:$commoncfg->{DATABASE}:$commoncfg->{DBHOST}",$commoncfg->{USERNAME},$commoncfg->{PASSWORD});
my %seqType = (
	0=>'Assembled',
	1=>'BAC-Insert',
	2=>'BAC-Circularized',
	3=>'BAC-NonVector',
	4=>'BAC-Gapped',
	5=>'Partial',
	6=>'Vector/Mixer',
	7=>'Mixer',
	8=>'SHORT',
	97=>'Piece',
	98=>'BES',
	99=>'Genome'
	);

my %bacAssignType = (
	0=>'',
	1=>'TagValid',
	2=>'BesValid',
	3=>'TagValid+BesValid',
	4=>'TagForced'
	);

my %seqDir = (
	0=>'NA',
	1=>'f',
	2=>'r'
	);

if (param ('seqId'))
{
	my $sequenceId = param ('seqId');
	my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$getSequences->execute($sequenceId);
	my @getSequences =  $getSequences->fetchrow_array();
	print header(-type=>'application/octet-stream',
		-attachment=> "$sequenceId-$getSequences[2]-$getSequences[3]-$getSequences[6].seq"
		);
	my $sequenceDetails = decode_json $getSequences[8];
	$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
	$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
	$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
	$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
	$getSequences[2] = $getSequences[0] unless ($getSequences[2]);
	$sequenceDetails->{'sequence'} =~ s/[^a-zA-Z0-9]//g;
	$sequenceDetails->{'sequence'} = multiLineSeq($sequenceDetails->{'sequence'},80);
	print ">$getSequences[0]-$getSequences[4]-$getSequences[2]-$seqType{$getSequences[3]}-$getSequences[6] $getSequences[5] bp $sequenceDetails->{'id'} $sequenceDetails->{'description'}\n$sequenceDetails->{'sequence'}";
}
elsif (param ('jobId'))
{
	my $jobId = param ('jobId');
	my $seqTypeNumber =  param ('seqType') || "0";
	print header(-type=>'application/octet-stream',
		-attachment=> "job-$jobId.$seqTypeNumber.seq"
		);
	my $getSequences;
	if($seqTypeNumber eq '0')
	{
		$getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o = 0 AND x = ?");
	}
	elsif($seqTypeNumber eq '1')
	{
		$getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND (o = 1 OR o = 2) AND x = ?");
	}
	elsif($seqTypeNumber eq '3')
	{
		$getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o = 3 AND x = ?");
	}
	elsif($seqTypeNumber eq '4')
	{
		$getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o = 4 AND x = ?");
	}
	elsif($seqTypeNumber eq 'bacId')
	{
		$getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND name != '' AND x = ?");
	}
	else
	{
		$getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o < 50 AND x = ?");
	}
	$getSequences->execute($jobId);
	while(my @getSequences =  $getSequences->fetchrow_array())
	{
		my $sequenceDetails = decode_json $getSequences[8];
		$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
		$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
		$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
		$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
		$getSequences[2] = $getSequences[0] unless ($getSequences[2]);
		$sequenceDetails->{'sequence'} =~ s/[^a-zA-Z0-9]//g;
		$sequenceDetails->{'sequence'} = multiLineSeq($sequenceDetails->{'sequence'},80);
		print ">$getSequences[0]-$getSequences[4]-$getSequences[2]-$seqType{$getSequences[3]}-$getSequences[6] $getSequences[5] bp $sequenceDetails->{'id'} $sequenceDetails->{'description'}\n$sequenceDetails->{'sequence'}";
	}		
}
elsif (param ('agpId'))
{
	my $agpId = param ('agpId');
	my $getAgp = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$getAgp->execute($agpId);
	my @getAgp =  $getAgp->fetchrow_array();
	if ($getAgp[2] =~ /\.agp$/)
	{
		print header(-type=>'application/octet-stream',
			-attachment=> "$getAgp[2]"
			);
	}
	else
	{
		print header(-type=>'application/octet-stream',
			-attachment=> "$getAgp[2].agp"
			);
	}
	print $getAgp[8];
}
elsif (param ('genomeId'))
{
	my $genomeId = param ('genomeId');
	my $getGenome = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$getGenome->execute($genomeId);
	my @getGenome =  $getGenome->fetchrow_array();
	print header(-type=>'application/octet-stream',
		-attachment=> "genome-$genomeId.$getGenome[2].seq"
		);
	my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o = 99 AND x = ?");
	$getSequences->execute($genomeId);
	while(my @getSequences =  $getSequences->fetchrow_array())
	{
		my $sequenceDetails = decode_json $getSequences[8];
		$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
		$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
		$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
		$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
		$sequenceDetails->{'sequence'} =~ s/[^a-zA-Z0-9]//g;
		$sequenceDetails->{'sequence'} = multiLineSeq($sequenceDetails->{'sequence'},80);
		if($sequenceDetails->{'id'} eq $getSequences[2])
		{
			print ">$sequenceDetails->{'id'} $sequenceDetails->{'description'}\n$sequenceDetails->{'sequence'}";
		}
		else
		{
			print ">$sequenceDetails->{'id'} $getSequences[2] $sequenceDetails->{'description'}\n$sequenceDetails->{'sequence'}";
		}
	}		
}
elsif(param ('libraryId'))
{
	my $libraryId = param ('libraryId');
	print header(-type=>'application/octet-stream',
		-attachment=>"library$libraryId.seq"
		);
	my $getClones = $dbh->prepare("SELECT * FROM clones WHERE libraryId = ? AND sequenced > 0 ORDER BY name");
	$getClones->execute($libraryId);
	while(my @getClones = $getClones->fetchrow_array())
	{
		my $getSequences;
		if($getClones[5])
		{
			$getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o < 50 AND (name LIKE ? OR name LIKE ?)");
			$getSequences->execute($getClones[1],$getClones[5]);
		}
		else
		{
			$getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o < 50 AND name LIKE ?");
			$getSequences->execute($getClones[1]);
		}
		while(my @getSequences =  $getSequences->fetchrow_array())
		{
			my $sequenceDetails = decode_json $getSequences[8];
			$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
			$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
			$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
			$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
			$sequenceDetails->{'sequence'} =~ s/[^a-zA-Z0-9]//g;
			$sequenceDetails->{'sequence'} = multiLineSeq($sequenceDetails->{'sequence'},80);
			print ">$getSequences[0]-$getSequences[4]-$getClones[1]-$getSequences[2]-$seqType{$getSequences[3]}-$getSequences[6] $getSequences[5] bp $sequenceDetails->{'id'} $sequenceDetails->{'description'}\n$sequenceDetails->{'sequence'}";
		}		
	}
}
elsif(param ('seqLibraryId'))
{
	my $seqLibraryId = param ('seqLibraryId');
	print header(-type=>'application/octet-stream',
		-attachment=>"libraryPool$seqLibraryId.html"
		);

	my $library=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$library->execute($seqLibraryId);
	my @library = $library->fetchrow_array();
	my $pools = '';
	my $pool=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'pool' AND x = ? ORDER BY name");
	$pool->execute($seqLibraryId);
	while (my @pool = $pool->fetchrow_array())
	{
		$pools = "
		<table border='1' cellspacing='1' width='100%'>
        <thead>
            <tr>
                <th><b>Pool Name</b></th>
                <th><b>Pool Size</b></th>
                <th><b>Pooling BACs</b></th>
                <th><b>Original BACs</b></th>
                <th><b>Notes</b></th>
                <th><b>Assembly jobId</b></th>
            </tr>
        </thead>
        <tbody>"
		unless($pools);

		my $jobIds;
		my $jobId=$dbh->prepare("SELECT * FROM link WHERE parent = ? AND type LIKE 'poolJob' ORDER BY child DESC");
		$jobId->execute($pool[0]);
		while(my @jobId = $jobId->fetchrow_array())
		{
			$jobIds .= "$jobId[1] ";
		}
		$jobIds = "None" unless ($jobIds);

		my $clones;
		my $originalClones;
		my $sequencedNumber = 0;
		my $notSequencedNumber = 0;
		my $clone=$dbh->prepare("SELECT clones.* FROM link,clones WHERE link.type LIKE 'poolClone' AND link.child = clones.name AND link.parent = ? ORDER BY clones.name");
		$clone->execute($pool[0]);
		while(my @clone = $clone->fetchrow_array())
		{
			$clones .= "<a title='$clone[5]'>$clone[1]</a>($clone[6]) ";
			$originalClones .= ($clone[5]) ? "<a title='$clone[1]'>$clone[5]</a>($clone[6]) ": "";
			($clone[6]) ? $sequencedNumber++ : $notSequencedNumber++;
		}
		$clones = "None" unless ($clones);
		my $totalCloneNumber = $sequencedNumber + $notSequencedNumber;
		$pools .= ($notSequencedNumber > 0) ? "<tr><td><a title='Id:$pool[0]'>$pool[2]</a></td>
		<td>$totalCloneNumber</td>
		<td>$clones</td>
		<td>$originalClones</td>
		<td><sup>Sequenced: $sequencedNumber; Not sequenced: $notSequencedNumber.</sup><br>$pool[8]</td>
		<td>$jobIds</td></tr>" : "<tr><td><a title='Id:$pool[0]'>$pool[2]</a></td>
		<td>$totalCloneNumber</td>
		<td>$clones</td>
		<td>$originalClones</td>
		<td><sup>Sequenced: $sequencedNumber.</sup><br>$pool[8]</td>
		<td>$jobIds</td></tr>";
	}
	$pools .= "</tbody></table>\n" if ($pools);
	print $pools;
}
elsif(param ('besLibraryId'))
{
	my $besLibraryId = param ('besLibraryId');
	print header(-type=>'application/octet-stream',
		-attachment=>"BESofLibrary$besLibraryId.seq"
		);
	my $getSequences = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'sequence' AND o = 98 AND x = ? ORDER BY name,id");
	$getSequences->execute($besLibraryId);
	while(my @getSequences =  $getSequences->fetchrow_array())
	{
		my $sequenceDetails = decode_json $getSequences[8];
		$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
		$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
		$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
		$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
		$sequenceDetails->{'sequence'} =~ s/[^a-zA-Z0-9]//g;
		$sequenceDetails->{'sequence'} = multiLineSeq($sequenceDetails->{'sequence'},80);
		print ">$getSequences[0]-$getSequences[4]-$seqType{$getSequences[3]}-$getSequences[2].$seqDir{$getSequences[6]} $getSequences[5] bp $sequenceDetails->{'id'} $sequenceDetails->{'description'}\n$sequenceDetails->{'sequence'}";
	}		
}
elsif(param ('cloneLibraryId'))
{
	my $cloneLibraryId = param ('cloneLibraryId');
	print header(-type=>'application/octet-stream',
		-attachment=>"cloneList$cloneLibraryId.txt"
		);
	my $poolClone;
	my $poolClones = $dbh->prepare("SELECT link.* FROM link,clones WHERE link.type LIKE 'poolClone' AND link.child = clones.name AND clones.libraryId = ? ORDER BY link.child");
	$poolClones->execute($cloneLibraryId);
	while(my @poolClones = $poolClones->fetchrow_array())
	{
		$poolClone->{$poolClones[1]} = $poolClones[0];
	}
	my $getClones = $dbh->prepare("SELECT * FROM clones WHERE libraryId = ?");
	$getClones->execute($cloneLibraryId);
	print "Clone\tOriginal\tSequence\n";
	while(my @getClones= $getClones->fetchrow_array())
	{
		if(exists $poolClone->{$getClones[1]})
		{
			print "$getClones[1]\t$getClones[5]\t$getClones[6]\tPooled\n";
		}
		else
		{
			print "$getClones[1]\t$getClones[5]\t$getClones[6]\n";
		}
	}
}
elsif(param ('tagLibraryId'))
{
	my $tagLibraryId = param ('tagLibraryId');
	print header(-type=>'application/octet-stream',
		-attachment=>"tagList$tagLibraryId.tag"
		);
	my $getTags = $dbh->prepare("SELECT * FROM matrix WHERE x = ? AND container LIKE 'tag' ORDER BY o");
	$getTags->execute($tagLibraryId);
	my $lastTag='';
	while(my @getTags= $getTags->fetchrow_array())
	{
		if($lastTag eq $getTags[3])
		{
			print "$getTags[2],";
		}
		else
		{
			if($lastTag)
			{
				print "\n$getTags[8] $getTags[3] $getTags[2],";
			}
			else
			{
				print "$getTags[8] $getTags[3] $getTags[2],";
			}
		}
		$lastTag = $getTags[3];
	}
}
elsif(param ('fpcId'))
{
	my $fpcId = param ('fpcId');
	print header(-type=>'application/octet-stream',
		-attachment=>"fpcCloneList$fpcId.txt"
		);
	my $getFpcClones = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'fpcClone' AND o = ? ORDER BY name");
	$getFpcClones->execute($fpcId);
	while(my @getFpcClones= $getFpcClones->fetchrow_array())
	{
		print ">$getFpcClones[2]\n$getFpcClones[8]\n";
	}
}
elsif(param ('assemblyCtgId'))
{
	my $assemblyCtgId = param ('assemblyCtgId');
	my $pseudo = param ('pseudo') || 0;
	my $assemblyCtg=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$assemblyCtg->execute($assemblyCtgId);
	my @assemblyCtg = $assemblyCtg->fetchrow_array();
	print header(-type=>'application/octet-stream',
		-attachment=>"assemblyCtg$assemblyCtgId.Ctg$assemblyCtg[2].seq"
		);
	my $gapLength = 100;

	if($pseudo)
	{
		print ">Ctg$assemblyCtg[2] (";
		my @assemblySeqList;
		my $lastAssemblySeq = "";
		foreach (split ",", $assemblyCtg[8])
		{
			/^-/ and next;
			$_ =~ s/[^a-zA-Z0-9]//g;
			push @assemblySeqList, $_;
			$lastAssemblySeq = $_;
		}
		my $ctgSequence = '';
		my $lastComponentType = '';
		foreach (@assemblySeqList)
		{
			my $assemblySeq=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$assemblySeq->execute($_);
			my @assemblySeq = $assemblySeq->fetchrow_array();
			my $assemblySequence=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$assemblySequence->execute($assemblySeq[5]);
			my @assemblySequence = $assemblySequence->fetchrow_array();
			my $sequenceDetails = decode_json $assemblySequence[8];
			$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
			$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
			$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
			$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
			$sequenceDetails->{'filter'} = '' unless (exists $sequenceDetails->{'filter'});
			$sequenceDetails->{'sequence'} =~ s/[^a-zA-Z0-9]//g;

			if($ctgSequence)
			{
				print ",$assemblySeq[2].$assemblySeq[5]";
			}
			else
			{
				print "$assemblySeq[2].$assemblySeq[5]";
			}
			my $assemblySeqStart;
			my $assemblySeqEnd;
			
			if($assemblySeq[8])
			{
				($assemblySeqStart,$assemblySeqEnd) = split ",",$assemblySeq[8];
			}
			else
			{
				$assemblySeqStart = 1;
				$assemblySeqEnd = $assemblySeq[6];
				my $updateAssemblyClone=$dbh->do("UPDATE matrix SET note = '$assemblySeqStart,$assemblySeqEnd' WHERE id = $assemblySeq[0]");
			}

			if ($assemblySeq[4] eq 1 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 4 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 5' 100 Ns
			{
				$ctgSequence .= 'N'x$gapLength if($ctgSequence && $lastComponentType ne 'U'); #only put 100 Ns while the gap is not at the end of contigs
				$lastComponentType = 'U';
			}

			if ($sequenceDetails->{'filter'})
			{
				my @filter = split",",$sequenceDetails->{'filter'};
				my @filterPos;
				my @position;
				my $start = $assemblySeqStart;
				my $end = $assemblySeqEnd;
				for my $filter(@filter)
				{
					@filterPos = split"-",$filter;
					next if ($assemblySeqStart > $filterPos[1]);
					last if ($assemblySeqEnd < $filterPos[0]);
					if ($assemblySeqStart >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
					{
						$start = 0;
						$assemblySeqEnd = 0;
						last;
					}
					if ($assemblySeqStart >= $filterPos[0] && $assemblySeqStart <= $filterPos[1])
					{
						$start = $filterPos[1]+1;
						next;
					}
					if ($assemblySeqEnd >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
					{
						$assemblySeqEnd = $filterPos[0]-1;
						last;
					}
					$end = $filterPos[0]-1;
					push @position,[$start,$end];
					$start = $filterPos[1]+1;
				}
				push @position,[$start,$assemblySeqEnd] if ($start > 0);
				if ($assemblySeq[7] =~ /^-/)
				{
					@position= reverse @position;
				}
				for my $position(@position)
				{
					my $sequence = substr($sequenceDetails->{'sequence'}, $position->[0] - 1, $position->[1] - $position->[0] + 1);		
					$sequence = reverseComplement($sequence) if($assemblySeq[7] < 0);
					$ctgSequence .= $sequence;
					$lastComponentType = 'D';
				}
			}
			else
			{
				my $sequence = substr($sequenceDetails->{'sequence'}, $assemblySeqStart - 1, $assemblySeqEnd - $assemblySeqStart + 1);		
				$sequence = reverseComplement($sequence) if($assemblySeq[7] < 0);
				$ctgSequence .= $sequence;
				$lastComponentType = 'D';
			}

			if ($assemblySeq[4] eq 2 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 5 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 3' 100 Ns
			{
				$ctgSequence .= 'N'x$gapLength if ($_ ne $lastAssemblySeq && $lastComponentType ne 'U'); #only put 100 Ns while the gap is not at the end of contigs
				$lastComponentType = 'U';
			}
		}
		$ctgSequence = multiLineSeq($ctgSequence,80);
		print ")\n$ctgSequence";
	}
	else
	{
		foreach (split ",", $assemblyCtg[8])
		{
			print ">HIDDEN-" if(/^-/);
			$_ =~ s/[^a-zA-Z0-9]//g;
			my $assemblySeq=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$assemblySeq->execute($_);
			my @assemblySeq = $assemblySeq->fetchrow_array();
			my $assemblySequence=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
			$assemblySequence->execute($assemblySeq[5]);
			my @assemblySequence = $assemblySequence->fetchrow_array();
			my $sequenceDetails = decode_json $assemblySequence[8];
			$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
			$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
			$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
			$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
			$sequenceDetails->{'filter'} = '' unless (exists $sequenceDetails->{'filter'});
			$sequenceDetails->{'sequence'} =~ s/[^a-zA-Z0-9]//g;
			$sequenceDetails->{'sequence'} = multiLineSeq($sequenceDetails->{'sequence'},80);
			print "$assemblySequence[2].$assemblySequence[0] $assemblySequence[4]-$seqType{$assemblySequence[3]} $assemblySequence[5] bp $sequenceDetails->{'id'} $sequenceDetails->{'description'}\n$sequenceDetails->{'sequence'}";
		}
	}
}
elsif(param ('assemblyCtgIdForAgp'))
{
	my $assemblyCtgIdForAgp = param ('assemblyCtgIdForAgp') || '';
	my $assemblyCtg = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$assemblyCtg->execute($assemblyCtgIdForAgp);
	my @assemblyCtg = $assemblyCtg->fetchrow_array();
	my $gapLength = 100;
	print header(-type=>'application/octet-stream',
		-attachment=>"Ctg$assemblyCtg[2].agp"
		);
	print "##agp-version 2.0\n";

	my @assemblySeqList;
	my $lastAssemblySeq = "";
	foreach (split ",", $assemblyCtg[8])
	{
		/^-/ and next;
		$_ =~ s/[^a-zA-Z0-9]//g;
		push @assemblySeqList, $_;
		$lastAssemblySeq = $_;
	}

	my $num = 1;
	my $begin = 1;
	my $lastComponentType = '';
	for (@assemblySeqList)
	{
		my $assemblySeq = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
		$assemblySeq->execute($_);
		my @assemblySeq = $assemblySeq->fetchrow_array();
		my ($assemblySeqStart,$assemblySeqEnd) = split",",$assemblySeq[8];
		my $sequence = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
		$sequence->execute($assemblySeq[5]);
		my @sequence = $sequence->fetchrow_array();
		my $sequenceDetails = decode_json $sequence[8];
		$sequenceDetails->{'filter'} = '' unless (exists $sequenceDetails->{'filter'});
		my $orient = ($assemblySeq[7] =~ /^-/) ? '-' : '+';

		if($num > 1 && $lastComponentType ne 'U') #only put 100 Ns while the gap is not at the end of contigs
		{
			if ($assemblySeq[4] eq 1 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 4 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 5' 100 Ns
			{
				print "Ctg$assemblyCtg[2]\t$begin\t",$begin+$gapLength-1,"\t$num\tU\t$gapLength\tcontig\tno\tna\n";
				$begin += $gapLength;
				$num++;
				$lastComponentType = 'U';
			}
		}

		if ($sequenceDetails->{'filter'})
		{
			my @filter = split",",$sequenceDetails->{'filter'};
			my @filterPos;
			my @position;
			my $start = $assemblySeqStart;
			my $end = $assemblySeqEnd;
			for my $filter(@filter)
			{
				@filterPos = split"-",$filter;
				next if ($assemblySeqStart > $filterPos[1]);
				last if ($assemblySeqEnd < $filterPos[0]);
				if ($assemblySeqStart >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
				{
					$start = 0;
					$assemblySeqEnd = 0;
					last;
				}
				if ($assemblySeqStart >= $filterPos[0] && $assemblySeqStart <= $filterPos[1])
				{
					$start = $filterPos[1]+1;
					next;
				}
				if ($assemblySeqEnd >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
				{
					$assemblySeqEnd = $filterPos[0]-1;
					last;
				}
				$end = $filterPos[0]-1;
				push @position,[$start,$end];
				$start = $filterPos[1]+1;
			}
			push @position,[$start,$assemblySeqEnd] if ($start > 0);
			if ($assemblySeq[7] =~ /^-/)
			{
				@position= reverse @position;
			}
			my $seqLength = 0;
			for my $position(@position)
			{
				$seqLength=$position->[1]-$position->[0]+1;
				if($sequence[3] > 50) #not BAC sequence
				{
					print "Ctg$assemblyCtg[2]\t$begin\t",$begin+$seqLength-1,"\t$num\tD\t$assemblySeq[2]\t$position->[0]\t$position->[1]\t$orient\n";
				}
				else
				{
					print "Ctg$assemblyCtg[2]\t$begin\t",$begin+$seqLength-1,"\t$num\tD\t$assemblySeq[2]\.$assemblySeq[5]\t$position->[0]\t$position->[1]\t$orient\n";
				}
				$begin += $seqLength;
				$num++;
				$lastComponentType = 'D';
			}
		}
		else
		{
			if($sequence[3] > 50) #not BAC sequence
			{
				print "Ctg$assemblyCtg[2]\t$begin\t",$begin+$assemblySeqEnd-$assemblySeqStart,"\t$num\tD\t$assemblySeq[2]\t$assemblySeqStart\t$assemblySeqEnd\t$orient\n";
			}
			else
			{
				print "Ctg$assemblyCtg[2]\t$begin\t",$begin+$assemblySeqEnd-$assemblySeqStart,"\t$num\tD\t$assemblySeq[2]\.$assemblySeq[5]\t$assemblySeqStart\t$assemblySeqEnd\t$orient\n";
			}
			$begin += $assemblySeqEnd-$assemblySeqStart+1;
			$num++;
			$lastComponentType = 'D';
		}
		if($_ ne $lastAssemblySeq && $lastComponentType ne 'U') #only put 100 Ns while the gap is not at the end of contigs
		{
			if ($assemblySeq[4] eq 2 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 5 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 3' 100 Ns
			{
				print "Ctg$assemblyCtg[2]\t$begin\t",$begin+$gapLength-1,"\t$num\tU\t$gapLength\tcontig\tno\tna\n";
				$begin += $gapLength;
				$num++;
				$lastComponentType = 'U';
			}
		}
	}
}
elsif(param ('assemblyId'))
{
	my $assemblyId = param ('assemblyId');
	my $chr = param('chr') || '0'; 
	my $unit = param('unit') || 'ctg'; 
	my $assembly=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$assembly->execute($assemblyId);
	my @assembly = $assembly->fetchrow_array();
	my $gapLength = 100;
	print header(-type=>'application/octet-stream',
		-attachment=>"assembly$assemblyId.$assembly[2].Chr$chr.$unit.seq"
		);

	if($unit eq 'chr')
	{
		my $preChr = 'na';
		my $chrUn = 1;
		my $chrSequence;
		my $lastComponentTypeOnChr;
		my $assemblyCtg=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'assemblyCtg' AND o = ? ORDER BY x,z,name");
		$assemblyCtg->execute($assemblyId);
		while(my @assemblyCtg = $assemblyCtg->fetchrow_array())
		{
			if ($chr ne 'all')
			{
				 next if ($assemblyCtg[4] ne $chr);
			}

			if($assemblyCtg[4] == 0)
			{
				my $chrUnNumber = sprintf "%0*d", 2, $chrUn;
				$chrUn++;
				print ">ChrUN$chrUnNumber (Ctg$assemblyCtg[2]-";

				my @assemblySeqList;
				my $lastAssemblySeq = "";
				foreach (split ",", $assemblyCtg[8])
				{
					/^-/ and next;
					$_ =~ s/[^a-zA-Z0-9]//g;
					push @assemblySeqList, $_;
					$lastAssemblySeq = $_;
				}

				my $ctgSequence = '';
				my $lastComponentType = '';
				foreach (@assemblySeqList)
				{
					my $assemblySeq=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
					$assemblySeq->execute($_);
					my @assemblySeq = $assemblySeq->fetchrow_array();
					my $assemblySequence=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
					$assemblySequence->execute($assemblySeq[5]);
					my @assemblySequence = $assemblySequence->fetchrow_array();
					my $sequenceDetails = decode_json $assemblySequence[8];
					$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
					$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
					$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
					$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
					$sequenceDetails->{'filter'} = '' unless (exists $sequenceDetails->{'filter'});
					$sequenceDetails->{'sequence'} =~ s/[^a-zA-Z0-9]//g;
					if($ctgSequence)
					{
						print ",$assemblySeq[2].$assemblySeq[5]";
					}
					else
					{
						print "$assemblySeq[2].$assemblySeq[5]";
					}
					$sequenceDetails->{'sequence'} =~ s/[^a-zA-Z0-9]//g;
					my $assemblySeqStart;
					my $assemblySeqEnd;
					if($assemblySeq[8])
					{
						($assemblySeqStart,$assemblySeqEnd) = split ",",$assemblySeq[8];
					}
					else
					{
						$assemblySeqStart = 1;
						$assemblySeqEnd = $assemblySeq[6];
						my $updateAssemblyClone=$dbh->do("UPDATE matrix SET note = '$assemblySeqStart,$assemblySeqEnd' WHERE id = $assemblySeq[0]");
					}

					if ($assemblySeq[4] eq 1 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 4 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 5' 100 Ns
					{
						$ctgSequence .= 'N'x$gapLength if ($ctgSequence && $lastComponentType ne 'U'); #only put 100 Ns while the gap is not at the end of contigs
						$lastComponentType = 'U';
					}
					
					if ($sequenceDetails->{'filter'})
					{
						my @filter = split",",$sequenceDetails->{'filter'};
						my @filterPos;
						my @position;
						my $start = $assemblySeqStart;
						my $end = $assemblySeqEnd;
						for my $filter(@filter)
						{
							@filterPos = split"-",$filter;
							next if ($assemblySeqStart > $filterPos[1]);
							last if ($assemblySeqEnd < $filterPos[0]);
							if ($assemblySeqStart >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
							{
								$start = 0;
								$assemblySeqEnd = 0;
								last;
							}
							if ($assemblySeqStart >= $filterPos[0] && $assemblySeqStart <= $filterPos[1])
							{
								$start = $filterPos[1]+1;
								next;
							}
							if ($assemblySeqEnd >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
							{
								$assemblySeqEnd = $filterPos[0]-1;
								last;
							}
							$end = $filterPos[0]-1;
							push @position,[$start,$end];
							$start = $filterPos[1]+1;
						}
						push @position,[$start,$assemblySeqEnd] if ($start > 0);
						if ($assemblySeq[7] =~ /^-/)
						{
							@position= reverse @position;
						}
						for my $position(@position)
						{
							my $sequence = substr($sequenceDetails->{'sequence'}, $position->[0] - 1, $position->[1] - $position->[0] + 1);		
							$sequence = reverseComplement($sequence) if($assemblySeq[7] < 0);
							$ctgSequence .= $sequence;
							$lastComponentType = 'D';
						}
					}
					else
					{
						my $sequence = substr($sequenceDetails->{'sequence'}, $assemblySeqStart - 1, $assemblySeqEnd - $assemblySeqStart + 1);		
						$sequence = reverseComplement($sequence) if($assemblySeq[7] < 0);
						$ctgSequence .= $sequence;
						$lastComponentType = 'D';
					}

					if ($assemblySeq[4] eq 2 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 5 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 3' 100 Ns
					{
						$ctgSequence .= 'N'x$gapLength if ($_ ne $lastAssemblySeq && $lastComponentType ne 'U'); #only put 100 Ns while the gap is not at the end of contigs
						$lastComponentType = 'U';
					}
				}
				$ctgSequence = multiLineSeq($ctgSequence,80);
				print ")\n$ctgSequence";
			}
			else
			{
				if ($preChr ne $assemblyCtg[4])
				{
					my $chrNumber = sprintf "%0*d", 2, $assemblyCtg[4];
					$chrSequence->{$preChr} = multiLineSeq($chrSequence->{$preChr},80);
					print ")\n$chrSequence->{$preChr}" if ($preChr ne 'na');
					print ">Chr$chrNumber (";
					$chrSequence->{$assemblyCtg[4]} = '';
					$lastComponentTypeOnChr->{$assemblyCtg[4]} = '';
					$preChr = $assemblyCtg[4];
				}
				else
				{
					$chrSequence->{$assemblyCtg[4]} .= 'N'x$gapLength if ($lastComponentTypeOnChr->{$assemblyCtg[4]} ne 'U');  #100 Ns between contigs
					$lastComponentTypeOnChr->{$assemblyCtg[4]} = 'U';
				}
				if(length ($chrSequence->{$assemblyCtg[4]}) > $gapLength)
				{
					print ";Ctg$assemblyCtg[2]-";
				}
				else
				{
					print "Ctg$assemblyCtg[2]-";
				}
				my $ctgSequence = '';
				foreach (split ",", $assemblyCtg[8])
				{
					/^-/ and next;
					$_ =~ s/[^a-zA-Z0-9]//g;
					my $assemblySeq=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
					$assemblySeq->execute($_);
					my @assemblySeq = $assemblySeq->fetchrow_array();
					my $assemblySequence=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
					$assemblySequence->execute($assemblySeq[5]);
					my @assemblySequence = $assemblySequence->fetchrow_array();
					my $sequenceDetails = decode_json $assemblySequence[8];
					$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
					$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
					$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
					$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
					$sequenceDetails->{'filter'} = '' unless (exists $sequenceDetails->{'filter'});
					$sequenceDetails->{'sequence'} =~ s/[^a-zA-Z0-9]//g;
					if($ctgSequence)
					{
						print ",$assemblySeq[2].$assemblySeq[5]";
					}
					else
					{
						print "$assemblySeq[2].$assemblySeq[5]";
					}
					$sequenceDetails->{'sequence'} =~ s/[^a-zA-Z0-9]//g;
					my $assemblySeqStart;
					my $assemblySeqEnd;
					if($assemblySeq[8])
					{
						($assemblySeqStart,$assemblySeqEnd) = split ",",$assemblySeq[8];
					}
					else
					{
						$assemblySeqStart = 1;
						$assemblySeqEnd = $assemblySeq[6];
						my $updateAssemblyClone=$dbh->do("UPDATE matrix SET note = '$assemblySeqStart,$assemblySeqEnd' WHERE id = $assemblySeq[0]");
					}

					if ($assemblySeq[4] eq 1 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 4 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 5' 100 Ns
					{
						$ctgSequence .= 'N'x$gapLength if ($lastComponentTypeOnChr->{$assemblyCtg[4]} ne 'U');
						$lastComponentTypeOnChr->{$assemblyCtg[4]} = 'U';
					}

					if ($sequenceDetails->{'filter'})
					{
						my @filter = split",",$sequenceDetails->{'filter'};
						my @filterPos;
						my @position;
						my $start = $assemblySeqStart;
						my $end = $assemblySeqEnd;
						for my $filter(@filter)
						{
							@filterPos = split"-",$filter;
							next if ($assemblySeqStart > $filterPos[1]);
							last if ($assemblySeqEnd < $filterPos[0]);
							if ($assemblySeqStart >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
							{
								$start = 0;
								$assemblySeqEnd = 0;
								last;
							}
							if ($assemblySeqStart >= $filterPos[0] && $assemblySeqStart <= $filterPos[1])
							{
								$start = $filterPos[1]+1;
								next;
							}
							if ($assemblySeqEnd >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
							{
								$assemblySeqEnd = $filterPos[0]-1;
								last;
							}
							$end = $filterPos[0]-1;
							push @position,[$start,$end];
							$start = $filterPos[1]+1;
						}
						push @position,[$start,$assemblySeqEnd] if ($start > 0);
						if ($assemblySeq[7] =~ /^-/)
						{
							@position= reverse @position;
						}
						for my $position(@position)
						{
							my $sequence = substr($sequenceDetails->{'sequence'}, $position->[0] - 1, $position->[1] - $position->[0] + 1);		
							$sequence = reverseComplement($sequence) if($assemblySeq[7] < 0);
							$ctgSequence .= $sequence;
							$lastComponentTypeOnChr->{$assemblyCtg[4]} = 'D';
						}
					}
					else
					{
						my $sequence = substr($sequenceDetails->{'sequence'}, $assemblySeqStart - 1, $assemblySeqEnd - $assemblySeqStart + 1);		
						$sequence = reverseComplement($sequence) if($assemblySeq[7] < 0);
						$ctgSequence .= $sequence;
						$lastComponentTypeOnChr->{$assemblyCtg[4]} = 'D';
					}

					if ($assemblySeq[4] eq 2 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 5 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 3' 100 Ns
					{
						$ctgSequence .= 'N'x$gapLength if ($lastComponentTypeOnChr->{$assemblyCtg[4]} ne 'U');
						$lastComponentTypeOnChr->{$assemblyCtg[4]} = 'U';
					}
				}
				$chrSequence->{$assemblyCtg[4]} .= $ctgSequence;
			}
		}
		$chrSequence->{$preChr} = multiLineSeq($chrSequence->{$preChr},80);
		print ")\n$chrSequence->{$preChr}" if ($preChr ne 'na');
	}
	else
	{
		my $assemblyCtg=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'assemblyCtg' AND o = ? ORDER BY x,z,name");
		$assemblyCtg->execute($assemblyId);
		while(my @assemblyCtg = $assemblyCtg->fetchrow_array())
		{
			if ($chr ne 'all')
			{
				 next if ($assemblyCtg[4] ne $chr);
			}
			my @assemblySeqList;
			my $lastAssemblySeq = "";
			foreach (split ",", $assemblyCtg[8])
			{
				/^-/ and next;
				$_ =~ s/[^a-zA-Z0-9]//g;
				push @assemblySeqList, $_;
				$lastAssemblySeq = $_;
			}

			print ">Ctg$assemblyCtg[2] (";
			my $ctgSequence = '';
			my $lastComponentType = '';
			foreach (@assemblySeqList)
			{
				my $assemblySeq=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
				$assemblySeq->execute($_);
				my @assemblySeq = $assemblySeq->fetchrow_array();
				my $assemblySequence=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
				$assemblySequence->execute($assemblySeq[5]);
				my @assemblySequence = $assemblySequence->fetchrow_array();
				my $sequenceDetails = decode_json $assemblySequence[8];
				$sequenceDetails->{'id'} = '' unless (exists $sequenceDetails->{'id'});
				$sequenceDetails->{'description'} = '' unless (exists $sequenceDetails->{'description'});
				$sequenceDetails->{'sequence'} = '' unless (exists $sequenceDetails->{'sequence'});
				$sequenceDetails->{'gapList'} = '' unless (exists $sequenceDetails->{'gapList'});
				$sequenceDetails->{'filter'} = '' unless (exists $sequenceDetails->{'filter'});
				$sequenceDetails->{'sequence'} =~ s/[^a-zA-Z0-9]//g;
				if($ctgSequence)
				{
					print ",$assemblySeq[2].$assemblySeq[5]";
				}
				else
				{
					print "$assemblySeq[2].$assemblySeq[5]";
				}
				my $assemblySeqStart;
				my $assemblySeqEnd;
				if($assemblySeq[8])
				{
					($assemblySeqStart,$assemblySeqEnd) = split ",",$assemblySeq[8];
				}
				else
				{
					$assemblySeqStart = 1;
					$assemblySeqEnd = $assemblySeq[6];
					my $updateAssemblyClone=$dbh->do("UPDATE matrix SET note = '$assemblySeqStart,$assemblySeqEnd' WHERE id = $assemblySeq[0]");
				}

				if ($assemblySeq[4] eq 1 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 4 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 5' 100 Ns
				{
					$ctgSequence .= 'N'x$gapLength if($ctgSequence && $lastComponentType ne 'U'); #only put 100 Ns while the gap is not at the end of contigs
					$lastComponentType = 'U';
				}

				if ($sequenceDetails->{'filter'})
				{
					my @filter = split",",$sequenceDetails->{'filter'};
					my @filterPos;
					my @position;
					my $start = $assemblySeqStart;
					my $end = $assemblySeqEnd;
					for my $filter(@filter)
					{
						@filterPos = split"-",$filter;
						next if ($assemblySeqStart > $filterPos[1]);
						last if ($assemblySeqEnd < $filterPos[0]);
						if ($assemblySeqStart >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
						{
							$start = 0;
							$assemblySeqEnd = 0;
							last;
						}
						if ($assemblySeqStart >= $filterPos[0] && $assemblySeqStart <= $filterPos[1])
						{
							$start = $filterPos[1]+1;
							next;
						}
						if ($assemblySeqEnd >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
						{
							$assemblySeqEnd = $filterPos[0]-1;
							last;
						}
						$end = $filterPos[0]-1;
						push @position,[$start,$end];
						$start = $filterPos[1]+1;
					}
					push @position,[$start,$assemblySeqEnd] if ($start > 0);
					if ($assemblySeq[7] =~ /^-/)
					{
						@position= reverse @position;
					}
					for my $position(@position)
					{
						my $sequence = substr($sequenceDetails->{'sequence'}, $position->[0] - 1, $position->[1] - $position->[0] + 1);		
						$sequence = reverseComplement($sequence) if($assemblySeq[7] < 0);
						$ctgSequence .= $sequence;
						$lastComponentType = 'D';
					}
				}
				else
				{
					my $sequence = substr($sequenceDetails->{'sequence'}, $assemblySeqStart - 1, $assemblySeqEnd - $assemblySeqStart + 1);		
					$sequence = reverseComplement($sequence) if($assemblySeq[7] < 0);
					$ctgSequence .= $sequence;
					$lastComponentType = 'D';
				}
				if ($assemblySeq[4] eq 2 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 5 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 3' 100 Ns
				{
					$ctgSequence .= 'N'x$gapLength if ($_ ne $lastAssemblySeq && $lastComponentType ne 'U'); #only put 100 Ns while the gap is not at the end of contigs
					$lastComponentType = 'U';
				}
			}
			$ctgSequence = multiLineSeq($ctgSequence,80);
			print ")\n$ctgSequence";
		}
	}
}
elsif(param ('assemblyIdForAgp'))
{
	my $assemblyIdForAgp = param ('assemblyIdForAgp');
	my $chr = param('chr') || '0'; 
	my $unit = param('unit') || 'ctg'; 
	my $element = param('element') || 'seq'; 
	my $assembly=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
	$assembly->execute($assemblyIdForAgp);
	my @assembly = $assembly->fetchrow_array();
	my $gapLength = 100;
	print header(-type=>'application/octet-stream',
		-attachment=>"assembly$assemblyIdForAgp.$assembly[2].Chr$chr.$unit-$element.agp"
		);
	print "##agp-version 2.0\n";
	if($unit eq 'chr')
	{
		my $preChr = 'na';
		my $chrUn = 1;
		my $num;
		my $begin;
		my $lastComponentType;
		my $assemblyCtg=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'assemblyCtg' AND o = ? ORDER BY x,z,name");
		$assemblyCtg->execute($assemblyIdForAgp);
		while(my @assemblyCtg = $assemblyCtg->fetchrow_array())
		{
			if ($chr ne 'all')
			{
				 next if ($assemblyCtg[4] ne $chr);
			}

			if($assemblyCtg[4] == 0)
			{
				$num->{0} = 1; #reset component number
				$begin->{0} = 1;
				$lastComponentType->{0} = '';
				my $chrUnNumber = sprintf "%0*d", 2, $chrUn;
				$chrUn++;
				if($element eq 'seq')
				{
					my @assemblySeqList;
					my $lastAssemblySeq = "";
					foreach (split ",", $assemblyCtg[8])
					{
						/^-/ and next;
						$_ =~ s/[^a-zA-Z0-9]//g;
						push @assemblySeqList, $_;
						$lastAssemblySeq = $_;
					}
					for (@assemblySeqList)
					{
						my $assemblySeq = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
						$assemblySeq->execute($_);
						my @assemblySeq = $assemblySeq->fetchrow_array();
						my ($assemblySeqStart,$assemblySeqEnd) = split",",$assemblySeq[8];
						my $sequence = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
						$sequence->execute($assemblySeq[5]);
						my @sequence = $sequence->fetchrow_array();
						my $sequenceDetails = decode_json $sequence[8];
						$sequenceDetails->{'filter'} = '' unless (exists $sequenceDetails->{'filter'});
						my $orient = ($assemblySeq[7] =~ /^-/) ? '-' : '+';

						if($num->{0} > 1 && $lastComponentType->{0} ne 'U') #only put 100 Ns while the gap is not at the end of contigs
						{
							if ($assemblySeq[4] eq 1 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 4 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 5' 100 Ns
							{
								print "ChrUN$chrUnNumber\t$begin->{0}\t",$begin->{0}+$gapLength-1,"\t$num->{0}\tU\t$gapLength\tcontig\tno\tna\n";
								$begin->{0} += $gapLength;
								$num->{0}++;
								$lastComponentType->{0} = 'U';
							}
						}

						if ($sequenceDetails->{'filter'})
						{
							my @filter = split",",$sequenceDetails->{'filter'};
							my @filterPos;
							my @position;
							my $start = $assemblySeqStart;
							my $end = $assemblySeqEnd;
							for my $filter(@filter)
							{
								@filterPos = split"-",$filter;
								next if ($assemblySeqStart > $filterPos[1]);
								last if ($assemblySeqEnd < $filterPos[0]);
								if ($assemblySeqStart >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
								{
									$start = 0;
									$assemblySeqEnd = 0;
									last;
								}
								if ($assemblySeqStart >= $filterPos[0] && $assemblySeqStart <= $filterPos[1])
								{
									$start = $filterPos[1]+1;
									next;
								}
								if ($assemblySeqEnd >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
								{
									$assemblySeqEnd = $filterPos[0]-1;
									last;
								}
								$end = $filterPos[0]-1;
								push @position,[$start,$end];
								$start = $filterPos[1]+1;
							}
							push @position,[$start,$assemblySeqEnd] if ($start > 0);
							if ($assemblySeq[7] =~ /^-/)
							{
								@position= reverse @position;
							}
							my $seqLength = 0;
							for my $position(@position)
							{
								$seqLength=$position->[1]-$position->[0]+1;
								if($sequence[3] > 50) #not BAC sequence
								{
									print "ChrUN$chrUnNumber\t$begin->{0}\t",$begin->{0}+$seqLength-1,"\t$num->{0}\tD\t$assemblySeq[2]\t$position->[0]\t$position->[1]\t$orient\n";
								}
								else
								{
									print "ChrUN$chrUnNumber\t$begin->{0}\t",$begin->{0}+$seqLength-1,"\t$num->{0}\tD\t$assemblySeq[2]\.$assemblySeq[5]\t$position->[0]\t$position->[1]\t$orient\n";
								}
								$begin->{0} += $seqLength;
								$num->{0}++;
								$lastComponentType->{0} = 'D';
							}
						}
						else
						{
							if($sequence[3] > 50) #not BAC sequence
							{
								print "ChrUN$chrUnNumber\t$begin->{0}\t",$begin->{0}+$assemblySeqEnd-$assemblySeqStart,"\t$num->{0}\tD\t$assemblySeq[2]\t$assemblySeqStart\t$assemblySeqEnd\t$orient\n";
							}
							else
							{
								print "ChrUN$chrUnNumber\t$begin->{0}\t",$begin->{0}+$assemblySeqEnd-$assemblySeqStart,"\t$num->{0}\tD\t$assemblySeq[2]\.$assemblySeq[5]\t$assemblySeqStart\t$assemblySeqEnd\t$orient\n";
							}
							$begin->{0} += $assemblySeqEnd-$assemblySeqStart+1;
							$num->{0}++;
							$lastComponentType->{0} = 'D';
						}
						if($_ ne $lastAssemblySeq && $lastComponentType->{0} ne 'U') #only put 100 Ns while the gap is not at the end of contigs
						{
							if ($assemblySeq[4] eq 2 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 5 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 3' 100 Ns
							{
								print "ChrUN$chrUnNumber\t$begin->{0}\t",$begin->{0}+$gapLength-1,"\t$num\tU\t$gapLength\tcontig\tno\tna\n";
								$begin->{0} += $gapLength;
								$num->{0}++;
								$lastComponentType->{0} = 'U';
							}
						}
					}
				}
				else
				{
					 #element eq 'ctg'
					 #no end Ns printed out
					print "ChrUN$chrUnNumber\t1\t",$assemblyCtg[7],"\t$num->{0}\tD\tCtg$assemblyCtg[2]\t1\t$assemblyCtg[7]\t+\n";
					$lastComponentType->{0} = 'D';
				}
			}
			else
			{
				my $chrNumber = sprintf "%0*d", 2, $assemblyCtg[4];
				if ($chrNumber eq $preChr && $lastComponentType->{$chrNumber} ne 'U')
				{
					#right gap
					print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$gapLength-1,"\t$num->{$chrNumber}\tU\t$gapLength\tcontig\tno\tna\n";
					$begin->{$chrNumber} += $gapLength;
					$num->{$chrNumber}++;
					$lastComponentType->{$chrNumber} = 'U';
				}
				else
				{
					$preChr = $chrNumber;
					$begin->{$chrNumber} = 1;
					$num->{$chrNumber} = 1;
					$lastComponentType->{$chrNumber} = '';
				}

				#sequence
				if($element eq 'seq')
				{
					for (split ",", $assemblyCtg[8])
					{
						/^-/ and next;
						$_ =~ s/[^a-zA-Z0-9]//g;
						my $assemblySeq = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
						$assemblySeq->execute($_);
						my @assemblySeq = $assemblySeq->fetchrow_array();
						my ($assemblySeqStart,$assemblySeqEnd) = split",",$assemblySeq[8];
						my $sequence = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
						$sequence->execute($assemblySeq[5]);
						my @sequence = $sequence->fetchrow_array();
						my $sequenceDetails = decode_json $sequence[8];
						$sequenceDetails->{'filter'} = '' unless (exists $sequenceDetails->{'filter'});
						my $orient = ($assemblySeq[7] =~ /^-/) ? '-' : '+';

						if($lastComponentType->{$chrNumber} ne 'U')
						{
							if ($assemblySeq[4] eq 1 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 8) # add 5' 100 Ns
							{
								print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$gapLength-1,"\t$num->{$chrNumber}\tU\t$gapLength\tcontig\tno\tna\n";
								$begin->{$chrNumber} += $gapLength;
								$num->{$chrNumber}++;
								$lastComponentType->{$chrNumber} = 'U';
							}

							if ($assemblySeq[4] eq 4 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7) # add 5' 100 Ns
							{
								print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$gapLength-1,"\t$num->{$chrNumber}\tU\t$gapLength\ttelomere\tno\tna\n";
								$begin->{$chrNumber} += $gapLength;
								$num->{$chrNumber}++;
								$lastComponentType->{$chrNumber} = 'U';
							}
						}
						if ($sequenceDetails->{'filter'})
						{
							my @filter = split",",$sequenceDetails->{'filter'};
							my @filterPos;
							my @position;
							my $start = $assemblySeqStart;
							my $end = $assemblySeqEnd;
							for my $filter(@filter)
							{
								@filterPos = split"-",$filter;
								next if ($assemblySeqStart > $filterPos[1]);
								last if ($assemblySeqEnd < $filterPos[0]);
								if ($assemblySeqStart >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
								{
									$start = 0;
									$assemblySeqEnd = 0;
									last;
								}
								if ($assemblySeqStart >= $filterPos[0] && $assemblySeqStart <= $filterPos[1])
								{
									$start = $filterPos[1]+1;
									next;
								}
								if ($assemblySeqEnd >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
								{
									$assemblySeqEnd = $filterPos[0]-1;
									last;
								}
								$end = $filterPos[0]-1;
								push @position,[$start,$end];
								$start = $filterPos[1]+1;
							}
							push @position,[$start,$assemblySeqEnd] if ($start > 0);
							if ($assemblySeq[7] =~ /^-/)
							{
								@position= reverse @position;
							}
							my $seqLength = 0;
							for my $position(@position)
							{
								$seqLength=$position->[1]-$position->[0]+1;
								if($sequence[3] > 50) #not BAC sequence
								{
									print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$seqLength-1,"\t$num->{$chrNumber}\tD\t$assemblySeq[2]\t$position->[0]\t$position->[1]\t$orient\n";
								}
								else
								{
									print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$seqLength-1,"\t$num->{$chrNumber}\tD\t$assemblySeq[2]\.$assemblySeq[5]\t$position->[0]\t$position->[1]\t$orient\n";
								}
								$begin->{$chrNumber} += $seqLength;
								$num->{$chrNumber}++;
								$lastComponentType->{$chrNumber} = 'D';
							}
						}
						else
						{
							if($sequence[3] > 50) #not BAC sequence
							{
								print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$assemblySeqEnd-$assemblySeqStart,"\t$num->{$chrNumber}\tD\t$assemblySeq[2]\t$assemblySeqStart\t$assemblySeqEnd\t$orient\n";
							}
							else
							{
								print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$assemblySeqEnd-$assemblySeqStart,"\t$num->{$chrNumber}\tD\t$assemblySeq[2]\.$assemblySeq[5]\t$assemblySeqStart\t$assemblySeqEnd\t$orient\n";
							}
							$begin->{$chrNumber} += $assemblySeqEnd-$assemblySeqStart+1;
							$num->{$chrNumber}++;
							$lastComponentType->{$chrNumber} = 'D';
						}
						if ($lastComponentType->{$chrNumber} ne 'U')
						{
							if ($assemblySeq[4] eq 2 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 7) # add 3' 100 Ns
							{
								print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$gapLength-1,"\t$num->{$chrNumber}\tU\t$gapLength\tcontig\tno\tna\n";
								$begin->{$chrNumber} += $gapLength;
								$num->{$chrNumber}++;
								$lastComponentType->{$chrNumber} = 'U';
							}
							if ($assemblySeq[4] eq 5 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 8) # add 3' 100 Ns
							{
								print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$gapLength-1,"\t$num->{$chrNumber}\tU\t$gapLength\ttelomere\tno\tna\n";
								$begin->{$chrNumber} += $gapLength;
								$num->{$chrNumber}++;
								$lastComponentType->{$chrNumber} = 'U';
							}
						}
					}
				}
				else
				{
					#element eq 'ctg'
					#check left end;
					my $startAssemblySeq = "";
					my $lastAssemblySeq = "";
					foreach (split ",", $assemblyCtg[8])
					{
						/^-/ and next;
						$_ =~ s/[^a-zA-Z0-9]//g;
						$startAssemblySeq = $_ unless ($startAssemblySeq);
						$lastAssemblySeq = $_;
					}
					my $assemblySeqStart = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
					$assemblySeqStart->execute($startAssemblySeq);
					my @assemblySeqStart = $assemblySeqStart->fetchrow_array();
					if($lastComponentType->{$chrNumber} ne 'U')
					{
						if ($assemblySeqStart[4] eq 1 || $assemblySeqStart[4] eq 3 || $assemblySeqStart[4] eq 8) # add 5' 100 Ns
						{
							print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$gapLength-1,"\t$num->{$chrNumber}\tU\t$gapLength\tcontig\tno\tna\n";
							$begin->{$chrNumber} += $gapLength;
							$num->{$chrNumber}++;
							$lastComponentType->{$chrNumber} = 'U';
						}

						if ($assemblySeqStart[4] eq 4 || $assemblySeqStart[4] eq 6 || $assemblySeqStart[4] eq 7) # add 5' 100 Ns
						{
							print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$gapLength-1,"\t$num->{$chrNumber}\tU\t$gapLength\ttelomere\tno\tna\n";
							$begin->{$chrNumber} += $gapLength;
							$num->{$chrNumber}++;
							$lastComponentType->{$chrNumber} = 'U';
						}
					}

					print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$assemblyCtg[7]-1,"\t$num->{$chrNumber}\tD\tCtg$assemblyCtg[2]\t1\t$assemblyCtg[7]\t+\n";
					$begin->{$chrNumber} += $assemblyCtg[7];
					$num->{$chrNumber}++;
					$lastComponentType->{$chrNumber} = 'D';
					#check right end;
					my $assemblySeqEnd = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
					$assemblySeqEnd->execute($lastAssemblySeq);
					my @assemblySeqEnd = $assemblySeqEnd->fetchrow_array();

					if($lastComponentType->{$chrNumber} ne 'U')
					{
						if ($assemblySeqEnd[4] eq 2 || $assemblySeqEnd[4] eq 3 || $assemblySeqEnd[4] eq 7) # add 3' 100 Ns
						{
							print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$gapLength-1,"\t$num->{$chrNumber}\tU\t$gapLength\tcontig\tno\tna\n";
							$begin->{$chrNumber} += $gapLength;
							$num->{$chrNumber}++;
							$lastComponentType->{$chrNumber} = 'U';
						}
						if ($assemblySeqEnd[4] eq 5 || $assemblySeqEnd[4] eq 6 || $assemblySeqEnd[4] eq 8) # add 3' 100 Ns
						{
							print "Chr$chrNumber\t$begin->{$chrNumber}\t",$begin->{$chrNumber}+$gapLength-1,"\t$num->{$chrNumber}\tU\t$gapLength\ttelomere\tno\tna\n";
							$begin->{$chrNumber} += $gapLength;
							$num->{$chrNumber}++;
							$lastComponentType->{$chrNumber} = 'U';
						}
					}
				}
			}
		}
	}
	else
	{
		my $assemblyCtg=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'assemblyCtg' AND o = ? ORDER BY x,z,name");
		$assemblyCtg->execute($assemblyIdForAgp);
		while(my @assemblyCtg = $assemblyCtg->fetchrow_array())
		{
			if ($chr ne 'all')
			{
				 next if ($assemblyCtg[4] ne $chr);
			}

			my @assemblySeqList;
			my $lastAssemblySeq = "";
			foreach (split ",", $assemblyCtg[8])
			{
				/^-/ and next;
				$_ =~ s/[^a-zA-Z0-9]//g;
				push @assemblySeqList, $_;
				$lastAssemblySeq = $_;
			}

			my $num = 1;
			my $begin = 1;
			my $lastComponentType = '';

			for (@assemblySeqList)
			{
				my $assemblySeq = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
				$assemblySeq->execute($_);
				my @assemblySeq = $assemblySeq->fetchrow_array();
				my ($assemblySeqStart,$assemblySeqEnd) = split",",$assemblySeq[8];
				my $sequence = $dbh->prepare("SELECT * FROM matrix WHERE id = ?");
				$sequence->execute($assemblySeq[5]);
				my @sequence = $sequence->fetchrow_array();
				my $sequenceDetails = decode_json $sequence[8];
				$sequenceDetails->{'filter'} = '' unless (exists $sequenceDetails->{'filter'});
				my $orient = ($assemblySeq[7] =~ /^-/) ? '-' : '+';
				if($num > 1 && $lastComponentType ne 'U') #only put 100 Ns while the gap is not at the end of contigs
				{
					if ($assemblySeq[4] eq 1 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 4 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 5' 100 Ns
					{
						print "Ctg$assemblyCtg[2]\t$begin\t",$begin+$gapLength-1,"\t$num\tU\t$gapLength\tcontig\tno\tna\n";
						$begin += $gapLength;
						$num++;
						$lastComponentType = 'U';
					}
				}

				if ($sequenceDetails->{'filter'})
				{
					my @filter = split",",$sequenceDetails->{'filter'};
					my @filterPos;
					my @position;
					my $start = $assemblySeqStart;
					my $end = $assemblySeqEnd;
					for my $filter(@filter)
					{
						@filterPos = split"-",$filter;
						next if ($assemblySeqStart > $filterPos[1]);
						last if ($assemblySeqEnd < $filterPos[0]);
						if ($assemblySeqStart >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
						{
							$start = 0;
							$assemblySeqEnd = 0;
							last;
						}
						if ($assemblySeqStart >= $filterPos[0] && $assemblySeqStart <= $filterPos[1])
						{
							$start = $filterPos[1]+1;
							next;
						}
						if ($assemblySeqEnd >= $filterPos[0] && $assemblySeqEnd <= $filterPos[1])
						{
							$assemblySeqEnd = $filterPos[0]-1;
							last;
						}
						$end = $filterPos[0]-1;
						push @position,[$start,$end];
						$start = $filterPos[1]+1;
					}
					push @position,[$start,$assemblySeqEnd] if ($start > 0);
					if ($assemblySeq[7] =~ /^-/)
					{
						@position= reverse @position;
					}
					my $seqLength = 0;
					for my $position(@position)
					{
						$seqLength=$position->[1]-$position->[0]+1;
						if($sequence[3] > 50) #not BAC sequence
						{
							print "Ctg$assemblyCtg[2]\t$begin\t",$begin+$seqLength-1,"\t$num\tD\t$assemblySeq[2]\t$position->[0]\t$position->[1]\t$orient\n";
						}
						else
						{
							print "Ctg$assemblyCtg[2]\t$begin\t",$begin+$seqLength-1,"\t$num\tD\t$assemblySeq[2]\.$assemblySeq[5]\t$position->[0]\t$position->[1]\t$orient\n";
						}
						$begin += $seqLength;
						$num++;
						$lastComponentType = 'D';
					}
				}
				else
				{
					if($sequence[3] > 50) #not BAC sequence
					{
						print "Ctg$assemblyCtg[2]\t$begin\t",$begin+$assemblySeqEnd-$assemblySeqStart,"\t$num\tD\t$assemblySeq[2]\t$assemblySeqStart\t$assemblySeqEnd\t$orient\n";
					}
					else
					{
						print "Ctg$assemblyCtg[2]\t$begin\t",$begin+$assemblySeqEnd-$assemblySeqStart,"\t$num\tD\t$assemblySeq[2]\.$assemblySeq[5]\t$assemblySeqStart\t$assemblySeqEnd\t$orient\n";
					}
					$begin += $assemblySeqEnd-$assemblySeqStart+1;
					$num++;
					$lastComponentType = 'D';
				}
				if($_ ne $lastAssemblySeq && $lastComponentType ne 'U') #only put 100 Ns while the gap is not at the end of contigs
				{
					if ($assemblySeq[4] eq 2 || $assemblySeq[4] eq 3 || $assemblySeq[4] eq 5 || $assemblySeq[4] eq 6 || $assemblySeq[4] eq 7 || $assemblySeq[4] eq 8) # add 3' 100 Ns
					{
						print "Ctg$assemblyCtg[2]\t$begin\t",$begin+$gapLength-1,"\t$num\tU\t$gapLength\tcontig\tno\tna\n";
						$begin += $gapLength;
						$num++;
						$lastComponentType = 'U';
					}
				}
			}
		}
	}
}
elsif (param ('assemblyIdForCtgList'))
{
	my $assemblyIdForCtgList = param ('assemblyIdForCtgList');
	print header(-type=>'application/octet-stream',
		-attachment=>"ctgList.$assemblyIdForCtgList.txt",
		);
	print "CTG\tNumber-of-assemblySeqs\tAssigned-chomosome#\tLength(bp)\tComment\n";
	my $assemblyCtg = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'assemblyCtg' AND o = ? ORDER BY x,z,y");
	$assemblyCtg->execute($assemblyIdForCtgList);
	while (my @assemblyCtg = $assemblyCtg->fetchrow_array())
	{
		my @seq=split",",$assemblyCtg[8];
		my $num=@seq;
		my $commentDetails;
		my $comment = $dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'comment' AND o = ?");
		$comment->execute($assemblyCtg[0]);
		my @comment = $comment->fetchrow_array();
		if ($comment->rows > 0)
		{
			$commentDetails = decode_json $comment[8];
			$commentDetails->{'description'} = '' unless (exists $commentDetails->{'description'});
			$commentDetails->{'description'} =~ s/[\n\r]/\\n/g;
			print "Ctg$assemblyCtg[2]\t$num\t$assemblyCtg[4]\t".commify($assemblyCtg[7])."\t'$commentDetails->{'description'}'\n";
		}
		else
		{
			print "Ctg$assemblyCtg[2]\t$num\t$assemblyCtg[4]\t".commify($assemblyCtg[7])."\t\n";
		}
	}
}
else
{
	print header(-type=>'text/html',-status=>'402 Invalid operation');
}
