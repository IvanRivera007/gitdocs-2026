Patches to Maple's LaTeX Macros
-------------------------------

This directory contains the latest versions of the style files that
are  used by LaTeX(2e) to process the files produced by worksheet menu
option  "File>>Export as>>LaTeX."   

These files replace the following files

${INSTALL_DIRECTORY}/etc/latex.txt		
${INSTALL_DIRECTORY}/etc/maple2e.sty
${INSTALL_DIRECTORY}/etc/mapleenv.def
${INSTALL_DIRECTORY}/etc/mapleenv.sty
${INSTALL_DIRECTORY}/etc/mapleplots.sty
${INSTALL_DIRECTORY}/etc/maplestyle.sty
${INSTALL_DIRECTORY}/etc/mapletab.sty
${INSTALL_DIRECTORY}/etc/mapleutil.sty

which are found on the Maple V Release 5.1 distribution.  The
actual changes that have occured are itemized below.

CHANGES since Release 5.1
-------------------------

1.  The following change fixes a latex macro bug in which 
certain maple input lines of a certain form  resulted in latex
syntax errors. 

File: mapleenv.sty

< %% $Revision: 1.6 $  (Shipped with Release 5.1)
---
> %% $Revision: 1.7 $  (This patch)
478c478
< \def\@doOneD#1{\MakeOther{\ }#1\egroup\unvbox\@inlinebox\relax\@mgobbleone}
---
> \def\@doOneD#1{\MakeOther{\ } #1\egroup\unvbox\@inlinebox\relax\@mgobbleone}
