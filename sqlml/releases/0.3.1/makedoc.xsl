<?xml version="1.0" encoding="utf-8"?>

<!--
    Converts an SQLML file into a DocBook fragment.
    Copyright (C) 2004  Daniel Larsson

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
  -->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		xmlns:sql="http://sqlml.sourceforge.net/xml/sql/1.0"
		xmlns:doc="http://sqlml.sourceforge.net/xml/doc/1.0"
		xmlns=""
                exclude-result-prefixes="doc sql"
                version="1.0">

  <xsl:preserve-space elements="*"/>
  <xsl:strip-space elements="xsl:*"/>



  <!--  ====================  Parameters  ====================  -->

  <!-- Don't change me -->
  <xsl:param name="dbname" select="sql:database/sql:name"/>

  <!-- Path to the generated table figure -->
  <xsl:param name="dbfigure" select="concat($dbname,'.png')"/>

  <!-- Top level element to use for the generated fragment -->
  <xsl:param name="topelement">section</xsl:param>


  <!--  ======================================================  -->



  <xsl:template match="/">
    <xsl:comment>
   This file generated from an XML file describing the database.

   Do not edit.
    </xsl:comment>
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="sql:name">
    <!-- Ignore the name, these are handled one level up the hierarchy -->
  </xsl:template>

  <xsl:template match="sql:name" mode="summary">
    <!-- Ignore the name, these are handled one level up the hierarchy -->
  </xsl:template>


  <xsl:template match="sql:database">
    <xsl:element name="{$topelement}">
      <xsl:attribute name="id">db-<xsl:value-of select="sql:name"/></xsl:attribute>
      <title>The <xsl:value-of select="sql:name"/> database</title>
      
      <para>
	The following figure shows the structure of the <xsl:value-of
	select="sql:name"/> database:
	<figure>
	  <title>The <xsl:value-of select="sql:name"/> tables</title>
	  <mediaobject>
	    <imageobject>
	      <imagedata format="PNG">
		<xsl:attribute name="fileref"><xsl:value-of select="$dbfigure"/></xsl:attribute>
	      </imagedata>
	    </imageobject>
	    <textobject><literallayout class="monospaced">
	    &lt;Insert database tables here>
	    </literallayout></textobject>
	  </mediaobject>
	</figure>
      </para>

      <table>
	<title>Tables in the <xsl:value-of select="sql:name"/> database</title>
	<tgroup cols="2">
	  <thead>
	    <row><entry>Table</entry><entry>Description</entry></row>
	  </thead>
	  <tbody>
	    <xsl:apply-templates mode="summary"/>
	  </tbody>
	</tgroup>
      </table>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>


  <xsl:template match="sql:table" mode="summary">
    <row>
      <entry>
	<link>
	  <xsl:attribute name="linkend">table-<xsl:value-of select="sql:name"/></xsl:attribute>
	  <xsl:value-of select="sql:name"/>
	</link>
      </entry>
      <entry><xsl:apply-templates select="doc:short"/></entry>
    </row>
  </xsl:template>


  <xsl:template match="sql:table">
    <section>
      <xsl:attribute name="id">table-<xsl:value-of select="sql:name"/></xsl:attribute>
      <title>Table <xsl:value-of select="sql:name"/></title>
      <xsl:apply-templates mode="doc"/>
      <table>
	<title>Columns in <xsl:value-of select="sql:name"/></title>
	<xsl:apply-templates select="sql:columns"/>
      </table>
    </section>
  </xsl:template>


  <xsl:template match="sql:columns">
    <tgroup cols="3">
      <thead>
	<row>
	  <entry>Column</entry>
	  <entry>Type</entry>
	  <entry>Description</entry>
	</row>
      </thead>
      <tbody>
	<xsl:apply-templates/>
      </tbody>
    </tgroup>
  </xsl:template>


  <xsl:template match="sql:column">
    <xsl:variable name="table" select="ancestor::sql:table"/>
    <xsl:variable name="tblname" select="$table/sql:name"/>
    <xsl:variable name="name" select="@name"/>
    <row>
      <xsl:attribute name="id">col-<xsl:value-of select="$tblname"/>-<xsl:value-of select="$name"/></xsl:attribute>
      <entry><xsl:value-of select="@name"/></entry>
      <entry><xsl:apply-templates select="sql:type"/></entry>
      <entry><xsl:apply-templates mode="doc"/></entry>
    </row>
  </xsl:template>


  <xsl:template match="sql:type">
    <xsl:choose>
      <xsl:when test="sql:key">
        <xsl:text>RELATION to </xsl:text>
	<link>
	  <xsl:attribute name="linkend">table-<xsl:value-of select="sql:key/@table"/></xsl:attribute>
	  <xsl:value-of select="sql:key/@table"/>
	</link>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="normalize-space(.)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template match="doc:short" mode="doc">
    <para><xsl:apply-templates/></para>
  </xsl:template>


  <xsl:template match="doc:description" mode="doc">
    <para><xsl:apply-templates mode="doc"/></para>
  </xsl:template>


  <xsl:template match="doc:column" mode="doc">
    <xsl:variable name="table" select="ancestor::sql:table"/>
    <xsl:variable name="tblname" select="$table/sql:name"/>
    <xsl:variable name="name" select="@name"/>
    <link linkend="col-{$tblname}-{$name}"><xsl:value-of select="@name"/></link>
  </xsl:template>


  <xsl:template match="doc:table" mode="doc">
    <xsl:variable name="name" select="@name"/>
    <link linkend="table-{$name}"><xsl:value-of select="@name"/></link>
  </xsl:template>


  <xsl:template match="*" mode="doc"/>


</xsl:stylesheet>
