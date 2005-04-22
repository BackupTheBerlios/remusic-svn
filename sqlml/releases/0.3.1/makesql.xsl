<?xml version="1.0" encoding="utf-8"?>

<!--
    Converts an SQLML file into SQL code creating the described tables.
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

  <xsl:template match="sql:database">
    <xsl:text>CREATE DATABASE IF NOT EXISTS </xsl:text>
    <xsl:value-of select="sql:name"/><xsl:text>;
</xsl:text>
    <xsl:text>USE </xsl:text><xsl:value-of select="sql:name"/><xsl:text>;
</xsl:text>
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="sql:table">
    <xsl:text>CREATE TABLE IF NOT EXISTS </xsl:text>
    <xsl:value-of select="sql:name"/>
    <xsl:text>(
</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>);
</xsl:text>
  </xsl:template>


  <xsl:template match="sql:column">
    <xsl:value-of select="@name"/>
    <xsl:apply-templates select="sql:type"/>
    <xsl:choose>
      <xsl:when test="sql:type/@primary-key = 'auto'">
        <xsl:text>,
        PRIMARY KEY (</xsl:text>
        <xsl:value-of select="@name"/>),
        INDEX (<xsl:value-of select="@name"/>)
      </xsl:when>
    </xsl:choose>
    <xsl:if test="position() != last()-1">
      <xsl:text>,</xsl:text>
    </xsl:if>
  </xsl:template>


  <xsl:template match="sql:type">
    <xsl:apply-templates/>
    <xsl:choose>
      <xsl:when test="@primary-key = 'auto'">
        <xsl:text>NOT NULL AUTO_INCREMENT</xsl:text>
      </xsl:when>
    </xsl:choose>
  </xsl:template>


  <xsl:template match="sql:key">
    <xsl:text>INT UNSIGNED,</xsl:text>
    <xsl:text>INDEX (</xsl:text>
    <xsl:value-of select="ancestor::sql:column/@name"/>),
    <xsl:text>FOREIGN KEY (</xsl:text>
    <xsl:value-of select="ancestor::sql:column/@name"/>
    <xsl:text>) REFERENCES </xsl:text>
    <xsl:value-of select="@table"/>
    <xsl:text>(</xsl:text><xsl:value-of select="@column"/>
    <xsl:text>) ON DELETE RESTRICT</xsl:text>
  </xsl:template>

  <xsl:template match="sql:name"/>
  <xsl:template match="doc:*"/>

</xsl:stylesheet>
