<?xml version="1.0" encoding="utf-8"?>

<!--
    Converts an SQLML file into a Python module.
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
                exclude-result-prefixes="doc"
                version="1.0">

  <xsl:output method="text"/>

  <xsl:template match="/">
    <xsl:text>"""This module describes the </xsl:text>
    <xsl:value-of select="sql:database/sql:name"/>
    <xsl:text> database.

This file is generated from an XML file describing the database.

Do not edit.
"""

import sqlquery

</xsl:text>

    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="sql:database">
    <xsl:text>_database = "</xsl:text>
    <xsl:value-of select="sql:name"/><xsl:text>"

</xsl:text>
    <xsl:apply-templates select="sql:table"/>
  </xsl:template>

  <xsl:template match="sql:table">
    <xsl:text>
# --- Table: </xsl:text>
    <xsl:value-of select="sql:name"/>
    <xsl:text>

</xsl:text>
    <xsl:apply-templates select="sql:columns"/>
    <xsl:text>
</xsl:text>
    <xsl:value-of select="sql:name"/>
    <xsl:text> = sqlquery.Table(_database, "</xsl:text>
    <xsl:value-of select="sql:name"/>
    <xsl:text>", (</xsl:text>
    <xsl:apply-templates select="sql:columns" mode="name"/>
    <xsl:text>))
</xsl:text>
  </xsl:template>

  <xsl:template match="sql:columns">
    <xsl:apply-templates select="sql:column"/>
  </xsl:template>

  <xsl:template match="sql:column" mode="name">
    <xsl:value-of select="ancestor::sql:table/sql:name"/>
    <xsl:text>_</xsl:text>
    <xsl:value-of select="@name"/>
    <xsl:if test="position() != last() - 1">
      <xsl:text>,</xsl:text>
    </xsl:if>
  </xsl:template>

  <xsl:template match="sql:column">
    <xsl:value-of select="ancestor::sql:table/sql:name"/>
    <xsl:text>_</xsl:text>
    <xsl:value-of select="@name"/>
    <xsl:choose>
      <xsl:when test="sql:type/sql:key">
        <xsl:text> = sqlquery.Relation("</xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:text>",</xsl:text>
        <xsl:value-of select="sql:type/sql:key/@table"/>
        <xsl:text>_</xsl:text>
        <xsl:value-of select="sql:type/sql:key/@column"/>
        <xsl:text>)
</xsl:text>
      </xsl:when>
      <xsl:when test="sql:type/@primary-key">
        <xsl:text> = sqlquery.PrimaryKey("</xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:text>")
</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text> = sqlquery.Column("</xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:text>")
</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template match="sql:type">
    <xsl:text>"</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>"</xsl:text>
  </xsl:template>


  <xsl:template match="sql:key">
    <xsl:value-of select="@column"/>),
  </xsl:template>


  <xsl:template match="*"/>


</xsl:stylesheet>
