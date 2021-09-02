<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" readOnly="0" labelsEnabled="0" simplifyDrawingTol="1" minScale="1e+08" simplifyDrawingHints="1" maxScale="0" simplifyMaxScale="1" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" simplifyLocal="1" version="3.10.4-A Coruña">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="singleSymbol" enableorderby="0" forceraster="0" symbollevels="0">
    <symbols>
      <symbol type="fill" force_rhr="0" name="0" alpha="1" clip_to_extent="1">
        <layer locked="0" class="SimpleFill" enabled="1" pass="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="105,187,50,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" name="name" value=""/>
              <Option name="properties"/>
              <Option type="QString" name="type" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property key="dualview/previewExpressions">
      <value>id</value>
    </property>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory lineSizeScale="3x:0,0,0,0,0,0" height="15" minScaleDenominator="0" scaleBasedVisibility="0" backgroundAlpha="255" penWidth="0" minimumSize="0" scaleDependency="Area" barWidth="5" enabled="0" width="15" labelPlacementMethod="XHeight" lineSizeType="MM" opacity="1" rotationOffset="270" backgroundColor="#ffffff" sizeType="MM" penAlpha="255" penColor="#000000" maxScaleDenominator="1e+08" sizeScale="3x:0,0,0,0,0,0" diagramOrientation="Up">
      <fontProperties style="" description="Noto Sans,9,-1,5,50,0,0,0,0,0"/>
      <attribute label="" color="#000000" field=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings linePlacementFlags="18" obstacle="0" dist="0" placement="1" zIndex="0" priority="0" showAll="1">
    <properties>
      <Option type="Map">
        <Option type="QString" name="name" value=""/>
        <Option name="properties"/>
        <Option type="QString" name="type" value="collection"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration type="Map">
      <Option type="Map" name="QgsGeometryGapCheck">
        <Option type="double" name="allowedGapsBuffer" value="0"/>
        <Option type="bool" name="allowedGapsEnabled" value="false"/>
        <Option type="QString" name="allowedGapsLayer" value=""/>
      </Option>
    </checkConfiguration>
  </geometryOptions>
  <fieldConfiguration>
    <field name="id">
      <editWidget type="UuidGenerator">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="roomA">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" name="IsMultiline" value="false"/>
            <Option type="bool" name="UseHtml" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="roomB">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" name="IsMultiline" value="false"/>
            <Option type="bool" name="UseHtml" value="false"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="sizeZ">
      <editWidget type="Range">
        <config>
          <Option type="Map">
            <Option type="bool" name="AllowNull" value="false"/>
            <Option type="double" name="Max" value="30"/>
            <Option type="double" name="Min" value="0"/>
            <Option type="int" name="Precision" value="2"/>
            <Option type="double" name="Step" value="1"/>
            <Option type="QString" name="Style" value="SpinBox"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="doorWay">
      <editWidget type="CheckBox">
        <config>
          <Option type="Map">
            <Option type="QString" name="CheckedState" value="1"/>
            <Option type="QString" name="UncheckedState" value="0"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="is_width">
      <editWidget type="CheckBox">
        <config>
          <Option type="Map">
            <Option type="QString" name="CheckedState" value="1"/>
            <Option type="QString" name="UncheckedState" value="0"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="width">
      <editWidget type="Range">
        <config>
          <Option type="Map">
            <Option type="bool" name="AllowNull" value="false"/>
            <Option type="double" name="Max" value="100"/>
            <Option type="double" name="Min" value="0"/>
            <Option type="int" name="Precision" value="2"/>
            <Option type="double" name="Step" value="1"/>
            <Option type="QString" name="Style" value="SpinBox"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" name="" field="id"/>
    <alias index="1" name="" field="roomA"/>
    <alias index="2" name="" field="roomB"/>
    <alias index="3" name="" field="sizeZ"/>
    <alias index="4" name="" field="doorWay"/>
    <alias index="5" name="" field="is_width"/>
    <alias index="6" name="" field="width"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" applyOnUpdate="0" field="id"/>
    <default expression="" applyOnUpdate="0" field="roomA"/>
    <default expression="" applyOnUpdate="0" field="roomB"/>
    <default expression="2" applyOnUpdate="0" field="sizeZ"/>
    <default expression="0" applyOnUpdate="1" field="doorWay"/>
    <default expression="0" applyOnUpdate="0" field="is_width"/>
    <default expression="0.8" applyOnUpdate="0" field="width"/>
  </defaults>
  <constraints>
    <constraint notnull_strength="2" unique_strength="0" constraints="1" field="id" exp_strength="0"/>
    <constraint notnull_strength="0" unique_strength="0" constraints="0" field="roomA" exp_strength="0"/>
    <constraint notnull_strength="0" unique_strength="0" constraints="0" field="roomB" exp_strength="0"/>
    <constraint notnull_strength="2" unique_strength="0" constraints="1" field="sizeZ" exp_strength="0"/>
    <constraint notnull_strength="0" unique_strength="0" constraints="0" field="doorWay" exp_strength="0"/>
    <constraint notnull_strength="0" unique_strength="0" constraints="0" field="is_width" exp_strength="0"/>
    <constraint notnull_strength="0" unique_strength="0" constraints="0" field="width" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" exp="" field="id"/>
    <constraint desc="" exp="" field="roomA"/>
    <constraint desc="" exp="" field="roomB"/>
    <constraint desc="" exp="" field="sizeZ"/>
    <constraint desc="" exp="" field="doorWay"/>
    <constraint desc="" exp="" field="is_width"/>
    <constraint desc="" exp="" field="width"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortOrder="0" sortExpression="">
    <columns>
      <column type="field" hidden="0" name="id" width="-1"/>
      <column type="field" hidden="0" name="roomA" width="-1"/>
      <column type="field" hidden="0" name="roomB" width="-1"/>
      <column type="field" hidden="0" name="sizeZ" width="-1"/>
      <column type="field" hidden="0" name="doorWay" width="-1"/>
      <column type="actions" hidden="1" width="-1"/>
      <column type="field" hidden="0" name="is_width" width="-1"/>
      <column type="field" hidden="0" name="width" width="-1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1">doors.ui</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field name="doorWay" editable="1"/>
    <field name="id" editable="1"/>
    <field name="is_width" editable="1"/>
    <field name="roomA" editable="0"/>
    <field name="roomB" editable="0"/>
    <field name="sizeZ" editable="1"/>
    <field name="width" editable="1"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="doorWay"/>
    <field labelOnTop="0" name="id"/>
    <field labelOnTop="0" name="is_width"/>
    <field labelOnTop="0" name="roomA"/>
    <field labelOnTop="0" name="roomB"/>
    <field labelOnTop="0" name="sizeZ"/>
    <field labelOnTop="0" name="width"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>id</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
