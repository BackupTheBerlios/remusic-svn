<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:sql="http://remus.sourceforge.net/xml/sql/1.0"
                xmlns:doc="http://remus.sourceforge.net/xml/doc/1.0"
                exclude-result-prefixes="doc"
                version="1.0">

  <xsl:output method="text"/>

  <xsl:template match="/">
    <xsl:text>"""This file generated from an XML file describing the database.

Do not edit.
"""
import remus.database

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
    <xsl:apply-templates select="sql:columns"/>
    <xsl:text>
</xsl:text>
    <xsl:value-of select="sql:name"/>
    <xsl:text> = remus.database.Table(_database, "</xsl:text>
    <xsl:value-of select="sql:name"/>
    <xsl:text>", (</xsl:text>
    <xsl:apply-templates select="sql:columns" mode="name"/>
    <xsl:text>))

# ----------


</xsl:text>
  </xsl:template>

  <xsl:template match="sql:columns">
    <xsl:apply-templates select="sql:column"/>
  </xsl:template>

  <xsl:template match="sql:column" mode="name">
    <xsl:value-of select="@sql:name"/>
    <xsl:if test="position() != last() - 1">
      <xsl:text>,</xsl:text>
    </xsl:if>
  </xsl:template>

  <xsl:template match="sql:column">
    <xsl:value-of select="@sql:name"/>
    <xsl:choose>
      <xsl:when test="sql:type/sql:key">
        <xsl:text> = remus.database.Relation("</xsl:text>
        <xsl:value-of select="@sql:name"/>
        <xsl:text>",</xsl:text>
        <xsl:value-of select="sql:type/sql:key/@sql:column"/>
        <xsl:text>)
</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text> = remus.database.Column("</xsl:text>
        <xsl:value-of select="@sql:name"/>
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
    <xsl:value-of select="@sql:column"/>),
  </xsl:template>


  <xsl:template match="*"/>


</xsl:stylesheet>
