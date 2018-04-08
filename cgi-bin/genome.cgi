#!/usr/bin/perl -w
use strict;
use CGI qw(:standard);
use CGI::Carp qw ( fatalsToBrowser ); 
use DBI;
use lib "lib/";
use lib "lib/pangu";
use pangu;
use userCookie;

my $userCookie = new userCookie;
my $userId = (cookie('cid')) ? $userCookie->checkCookie(cookie('cid')) : 0;
if(!$userId)
{
	print header;
	print <<eof;
	<h2>Error</h2>
	Please <a onclick="openDialog('login.cgi');">login</a> first!
	<script type="text/javascript">
		openDialog('login.cgi');
		loadingHide();
	</script>
eof
    exit;
}

my $commoncfg = readConfig("main.conf");
my $dbh=DBI->connect("DBI:mysql:$commoncfg->{DATABASE}:$commoncfg->{DBHOST}",$commoncfg->{USERNAME},$commoncfg->{PASSWORD});
my $objectComponent;
$objectComponent->{0} = "Unknown";
$objectComponent->{1} = "Chr-Seq";
$objectComponent->{2} = "Ctg-Seq";

undef $/;# enable slurp mode
my $html = <DATA>;

my $genomes = '';
my %yesOrNo = ( 0=>'No', 1=>'Yes' );
my $allGenome=$dbh->prepare("SELECT * FROM matrix WHERE container Like 'genome'");
$allGenome->execute();
while (my @allGenome = $allGenome->fetchrow_array())
{
	$allGenome[8] = escapeHTML($allGenome[8]);
	$allGenome[8] =~ s/\n/<br>/g;
	my $relatedAssemblies = '';
	my $relatedAssembly=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'assembly' AND (x = $allGenome[0] OR y = $allGenome[0])");
	$relatedAssembly->execute();
	while (my @relatedAssembly = $relatedAssembly->fetchrow_array())
	{
	
		$relatedAssemblies .= (length $relatedAssembly[2] > 12) ? "<li><a onclick='openDialog(\"assemblyView.cgi?assemblyId=$relatedAssembly[0]\")' title='$relatedAssembly[2]'>" . substr($relatedAssembly[2],0,10 )."...</a></li>" : "<li><a onclick='openDialog(\"assemblyView.cgi?assemblyId=$relatedAssembly[0]\")' title='$relatedAssembly[2]'>" . $relatedAssembly[2] ."</a></li>";
	}

	my $relatedLibraries = '';
	if ($allGenome[6])
	{
		my $relatedLibrary=$dbh->prepare("SELECT * FROM matrix WHERE id = ?");
		$relatedLibrary->execute($allGenome[6]);
		my @relatedLibrary = $relatedLibrary->fetchrow_array();
		$relatedLibraries = "<a onclick='openDialog(\"libraryView.cgi?libraryId=$allGenome[6]\")'>$relatedLibrary[2]</a> ";
	}
	
	my $agpAvailable = "";
	my $agpList=$dbh->prepare("SELECT * FROM matrix WHERE container LIKE 'agp' AND x = ? ORDER BY o");
	$agpList->execute($allGenome[0]);
	while (my @agpList = $agpList->fetchrow_array())
	{
		$agpAvailable .= ($agpAvailable) ? "<br> <a href='download.cgi?agpId=$agpList[0]' target='hiddenFrame' title='$objectComponent->{$agpList[5]} AGP v.$agpList[3]'>$agpList[2]</a>" : " Available AGP:<br> <a href='download.cgi?agpId=$agpList[0]' target='hiddenFrame' title='$objectComponent->{$agpList[5]} AGP v.$agpList[3]'>$agpList[2]</a>";
	}

	$genomes = "<form id='genomeList$$' name='genomeList$$'>
		<table id='genomes$$' class='display' style='width: 100%;'>
			<thead>
				<tr>
					<th>
						<input type='checkbox' id='checkAllBox$$' name='checkAllBox$$' value='Check all' checked='checked' onClick='checkAll(\"itemId\");return false;' title='Check all'>
						<input type='checkbox' id='uncheckAllBox$$' name='uncheckAllBox$$' value='Uncheck all' onClick='uncheckAll(\"itemId\");return false;' title='Uncheck all'>
					</th>
					<th style='text-align:left'><b>Genome</b></th>
					<th style='text-align:left'><b>Sequences</b></th>
					<th style='text-align:left'><b>For Reassembly</b></th>
					<th style='text-align:left'><b>As Reference</b></th>
					<th style='text-align:left'><b>Related Library</b></th>
					<th style='text-align:left'><b>Related Assemblies</b></th>
					<th style='text-align:left'><b>Creator</b></th>
					<th style='text-align:left'><b>Creation Date</b></th>
				</tr>
			</thead>
			<tbody>" unless($genomes);
	$genomes .= "<tr>
		<td style='text-align:center;'><input type='checkbox' id='genomeList$allGenome[0]$$' name='itemId' value='$allGenome[0]'></td>
		<td title='Genome'><a id='genomeId$allGenome[0]$$' onclick='openDialog(\"genomeView.cgi?genomeId=$allGenome[0]\")' title='View'>$allGenome[2]</a></td>
		<td title='Click to download $allGenome[3] Sequences'><a href='download.cgi?genomeId=$allGenome[0]' target='hiddenFrame'>$allGenome[3]</a></td>
		<td>$yesOrNo{$allGenome[4]}. $agpAvailable</td>
		<td title='As a reference for assembly'>$yesOrNo{$allGenome[5]}</td>
		<td title='Related Library'>$relatedLibraries</td>
		<td><ul class='gridGenomeList'>$relatedAssemblies</ul></td>
		<td title='Creator'>$allGenome[9]</td>
		<td title='Creation date'>$allGenome[10]</td>
		</tr>";
}
$genomes .= "</tbody></table></form>\n" if($genomes);
my $button = "<div class='ui-state-highlight ui-corner-all' style='padding: 0 .7em;'>
	<button style='float: right; margin-top: .3em; margin-right: .3em;' onclick='openDialog(\"alignmentLoadForm.cgi\")'>Load Tabular Alignment</button>
	<button style='float: right; margin-top: .3em; margin-right: .3em;' onclick='openDialog(\"alignmentForm.cgi\")'>Run Alignment</button>";
$button .= "<button style='float: right; margin-top: .3em; margin-right: .3em;' onclick='openDialogForm(\"itemDeleteForm.cgi\",\"genomeList$$\")'>Delete</button>" if($allGenome->rows > 0);
$button .= "<button style='float: right; margin-top: .3em; margin-right: .3em;' onclick='openDialogForm(\"genomeMergeForm.cgi\",\"genomeList$$\")'>Merge</button>" if($allGenome->rows > 1);
$button .= "<button style='float: right; margin-top: .3em; margin-right: .3em;' onclick='openDialogForm(\"genomeSplitForm.cgi\",\"genomeList$$\")'>Split</button>
	<button style='float: right; margin-top: .3em; margin-right: .3em;' onclick='openDialog(\"genomeNew.cgi\")'>New Genome</button>
	<button style='float: right; margin-top: .3em; margin-right: .3em;' onclick='refresh(\"general\")'>Refresh</button>
	<input style='float: right;; margin-top: .3em; margin-right: .3em;' class='ui-widget-content ui-corner-all' name='seqName' id='searchSeqName$$' size='16' type='text' maxlength='32' VALUE='' placeholder='Search Seq' />
	";
$button .= "<h2>Genomes</h2>";

unless($genomes)
{
	$button .= "<p class='ui-state-error ui-corner-all' style='padding: .7em;'><span class='ui-icon ui-icon-alert' style='float: left; margin-right: .3em;'></span>
			<strong>No genome, please upload one!</strong></p>";
}
$button .= "</div>\n";

$html =~ s/\$button/$button/g;
$html =~ s/\$genomes/$genomes/g;
$html =~ s/\$\$/$$/g;


print header(-cookie=>cookie(-name=>'general',-value=>4));
print $html;

__DATA__
$button
$genomes
<style>
	.gridGenomeList { list-style-type: none; display:inline-block;margin: 0; padding: 0; width: 100%; }
	.gridGenomeList li { margin: 3px 3px 3px 0; padding: 1px; float: left; width: 100px; text-align: left; }
</style>
<script>
buttonInit();
$( "#genomes$$" ).dataTable({
	"scrollY": "600px",
	"scrollCollapse": true,
	"paging": false,
	"columnDefs": [
    { "orderable": false, "targets": 0 }
  ]
});
$( "#searchSeqName$$" ).autocomplete({
	source: "autoSeqSearch.cgi",
	minLength: 4,
	select: function( event, ui ) {
		openDialog("seqView.cgi?seqId=" + ui.item.id);
	}
});
loadingHide();
</script>