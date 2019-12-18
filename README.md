# python-sie-ink2
A SIE parser that generates an INK2R from an exported sie file

## Basic concept
The Swedish IRS publish a set of codes every year. These codes then map towards the fields in the INK2R.

The document for fiscal year (2019 INK2R_2019P4.pdf) is part of the archive
https://www.skatteverket.se/download/18.32a87cee16d2b11f30e528e/1571743605740/Nyheter_from_beskattningsperiod_2019P4.zip

The mapping for 2019 can be seen in the file <i>input/ink2r_2019.txt</i>

For instance the INK2R 2.26 looks like,

<pre>
[IRS code] ; [INK2R] ; [Description]
7281 ; 2.26 ; Kassa och bank Kassa, bank och redovisningsmedel
</pre>

Most SIE files exported from your accounting program then includes a SRU code. These SRU codes then map your book keeping accounts to the
above references IRS codes.

For instance,
<pre>
#SRU 1910 7281
#KONTO 1920 "Plusgiro"
#SRU 1920 7281
#KONTO 1930 "Checkräkningskonto"
#SRU 1930 7281
</pre>
implies that the accounts 1910, 1920, 1930 all map towards 7281 and thus all contributes to the field 2.26 in your INK2R

By parsing the IRS codes (for 2019) and by parsing the exported SIE file (2019) you can generate the INK2R form.

## Pre requisites

1. Your current record of accounting is correct and finalized for the year (including result, final tax, accrual etc.)

2. Your accounting software exports SRU codes to the SIE file.

Not all commercial software exports SRU codes. Visma eEkonomi does not, but Bokio does.
Free software from Bokio at https://www.bokio.se/

If you lack SRU codes, you might be able to import your SIE file in for instance BOKIO and then export it again.

# Run sample
There is only one argument to the script and that is the exported SIE file. An arbitrary example SIE file is located in the samples folder. Pass you SIE file as,

<pre>
./main.py --sie samples/sie4_sample.se
</pre>

The output (INK2R result) is saved in the folder <i>output</i>
