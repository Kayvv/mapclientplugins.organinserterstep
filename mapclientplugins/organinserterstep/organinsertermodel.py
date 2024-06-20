import csv
import json
import os

from cmlibs.utils.zinc.general import ChangeManager
from cmlibs.utils.zinc.field import findOrCreateFieldGroup, findOrCreateFieldCoordinates,\
    findOrCreateFieldStoredString
from cmlibs.zinc.context import Context
from cmlibs.zinc.field import Field
from cmlibs.zinc.node import Node
from cmlibs.zinc.result import RESULT_OK

from scaffoldfitter.fitter import Fitter
from scaffoldfitter.fitterstepalign import FitterStepAlign
from scaffoldfitter.fitterstepfit import FitterStepFit


class OrganInserter(object):
    def __init__(self, input_model_file, input_data_files, output_directory):
        # Initializing with input parameters
        self._input_data_files = input_data_files
        marker_coordinates = MarkerCoordinates(input_model_file, output_directory)

        # Write annotations to a CSV file
        # self.write_annotations(output_directory)

        # Transform and add organ groups
        self._output_filenames = []
        for file in input_data_files:
            if 'colon' in file.lower():
                self._output_filenames.append(file)
                self.add_organ_group(file)
            else:
                organ_transformer = OrganTransformer(file, marker_coordinates.output_filename(), output_directory)
                self._output_filenames.append(organ_transformer.output_filename())
                self.add_organ_group(organ_transformer.output_filename())

    def get_output_file_name(self):
        return self._output_filenames

    # Method to extract organ name from file name
    def get_organ_name(self, filename):
        organsList = ['lung', 'heart', 'brainstem', 'stomach', 'bladder']
        filename_base = os.path.basename(filename).split('.')[0]
        for organ_name in organsList:
            if organ_name in filename_base.lower():
                return organ_name
        else:
            return filename_base

    # Method to write annotations to a CSV file
    def write_annotations(self, output_directory):
        DOI = ["https://doi.org/10.26275/yibc-wyu2", "https://doi.org/10.26275/dqpf-gqdt",
               "https://doi.org/10.26275/rets-qdch", "https://doi.org/10.26275/dqpf-gqdt",
               "https://doi.org/10.26275/yum2-z4uf", "https://doi.org/10.26275/xq3h-ba2b", "colon"]
        organ_names = ['whole-body']
        for filename in self._input_data_files:
            organ_names.append(self.get_organ_name(filename))

        # Writing annotations to CSV
        annotation_file = os.path.join(output_directory, 'organinserter_annotations.csv')
        with open(annotation_file, 'w', newline='') as fout:
            writer = csv.writer(fout)
            writer.writerow(['Organ name', 'Source', 'File name', 'Transformed file name'])
            writer.writerow([organ_names[0], DOI[0], 'whole_body.exf', 'whole_body.exf'])
            for c, filename in enumerate(self._input_data_files):
                filenamebase = os.path.basename(filename)
                writer.writerow([organ_names[c + 1], DOI[c + 1], filenamebase,
                                 filenamebase.split('.')[0] + '_transfromed_fit1.exf'])

    # Method to add organ group
    def add_organ_group(self, filename):
        # Creating context and region
        context = Context('organGroup')
        region = context.createRegion()
        region.readFile(filename)
        field_module = region.getFieldmodule()
        mesh = field_module.findMeshByDimension(3)
        with ChangeManager(field_module):
            # Creating field group for the organ
            field_group = field_module.createFieldGroup()
            organ_name = self.get_organ_name(filename)
            field_group.setName(organ_name)
            field_group.setSubelementHandlingMode(field_group.SUBELEMENT_HANDLING_MODE_FULL)
            mesh_group = field_group.createMeshGroup(mesh)
            is_organ = field_module.createFieldConstant(1)
            mesh_group.addElementsConditional(is_organ)
            sir = region.createStreaminformationRegion()
            srm = sir.createStreamresourceMemory()
            sir.setResourceGroupName(srm, organ_name)
            region.write(sir)
            region.writeFile(filename)


# Base class for output files
class BaseOutputFile(object):

    def __init__(self):
        self._output_filename = None

    def output_filename(self):
        return self._output_filename


# Class for transforming organ models
class OrganTransformer(BaseOutputFile):

    def __init__(self, input_zinc_model_file, input_zinc_data_file, output_directory):
        super().__init__()
        # Initializing Fitter with input files
        self._fitter = Fitter(input_zinc_model_file, input_zinc_data_file)
        self._fitter.load()
        self.set_model_coordinates_field()

        # Generating output filename
        file_basename = os.path.basename(input_zinc_model_file).split('.')[0]
        filename = file_basename + '_transformed'
        path = output_directory
        self._output_filename = os.path.join(path, filename)

        # Setting up transformation steps
        self._currentFitterStep = FitterStepAlign()
        self._fitter.addFitterStep(self._currentFitterStep)
        self._currentFitterStep.setAlignMarkers(True)
        self._currentFitterStep.run(modelFileNameStem=self._output_filename)

        self._currentFitterStep = FitterStepFit()
        self._fitter.addFitterStep(self._currentFitterStep)
        self._currentFitterStep.setGroupStrainPenalty(None, [0.001])
        self._currentFitterStep.setGroupCurvaturePenalty(None, [200.0])
        self._currentFitterStep.setGroupDataWeight(None, 1000.0)

        # Running transformation
        print("Transforming organ ({}) ... It may take a minute".format(file_basename))
        self._currentFitterStep.run(modelFileNameStem=self._output_filename)
        self._output_filename = self._output_filename + '_fit1.exf'
        print('Transformation is done')

    # Method to set model coordinates field
    def set_model_coordinates_field(self):
        field_module = self._fitter.getFieldmodule()
        modelCoordinatesFieldName = "coordinates"
        field = field_module.findFieldByName(modelCoordinatesFieldName)
        if field.isValid():
            self._fitter.setModelCoordinatesFieldByName(modelCoordinatesFieldName)


# Class for handling marker coordinates
class MarkerCoordinates(BaseOutputFile):
    def __init__(self, input_scaffold_file, output_directory):
        super().__init__()
        # Creating context and region
        self._context = Context('markerBodyCoordinates')
        self._region = self._context.createRegion()
        self._region.setName('bodyRegion')
        self._field_module = self._region.getFieldmodule()
        self._scaffold_file = input_scaffold_file
        self._model_coordinates_field = None
        self._marker_region = None

        # Loading scaffold file and discovering coordinate fields
        self._load()
        self._get_marker_coordinates()
        marker_region = self._get_marker_region()
        self._save(marker_region, output_directory)

    def _discover_coordinate_fields(self):
        field = None
        if self._model_coordinates_field:
            field = self._field_module.findFieldByName(self._model_coordinates_field)
        else:
            mesh = self._get_highest_dimension_mesh()
            element = mesh.createElementiterator().next()
            if element.isValid():
                field_cache = self._field_module.createFieldcache()
                field_cache.setElement(element)
                field_iter = self._field_module.createFielditerator()
                field = field_iter.next()
                while field.isValid():
                    if field.isTypeCoordinate() and (field.getNumberOfComponents() == 3) \
                            and (field.castFiniteElement().isValid()):
                        if field.isDefinedAtLocation(field_cache):
                            break
                    field = field_iter.next()
                else:
                    field = None
        if field:
            self._set_model_coordinates_field(field)

    def get_marker_fields(self):
        marker_group_names = []
        marker_name = False
        marker_location_name = False
        marker_group_name = False
        field_iter = self._field_module.createFielditerator()
        field = field_iter.next()
        while field.isValid():
            field_name = field.getName()
            if 'marker' in field_name.lower() and '_' in field_name.lower():
                marker_group_name = field_name
                marker_group_names.append(marker_group_name)
                if 'name' in field_name.lower():
                    marker_name = field_name
                elif 'location' in field_name.lower():
                    marker_location_name = field_name
                elif '.' not in field_name:
                    marker_group_name = field_name
            field = field_iter.next()
        if all([marker_name, marker_location_name, marker_group_names]):
            return marker_location_name, marker_name, marker_group_names
        else:
            raise AssertionError('Could not find marker fields')

    def _get_highest_dimension_mesh(self):
        for d in range(2, -1, -1):
            mesh = self._mesh[d]
            if mesh.getSize() > 0:
                return mesh
        return None

    def _load(self):
        result = self._region.readFile(self._scaffold_file)
        assert result == RESULT_OK, "Failed to load model file" + str(self._scaffold_file)
        self._mesh = [self._field_module.findMeshByDimension(d + 1) for d in range(3)]
        self._discover_coordinate_fields()

    def _save(self, region, output_directory):
        filename = os.path.basename(self._scaffold_file).split('.')[0] + '_marker_coordinates.exnode'
        path = output_directory
        self._output_filename = os.path.join(path, filename)
        region.writeFile(self._output_filename)

    def _get_marker_coordinates(self):
        field_cache = self._field_module.createFieldcache()
        nodes = self._field_module.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)

        marker_location_name, marker_name, marker_group_names = self.get_marker_fields()

        markerLocation = self._field_module.findFieldByName(marker_location_name)
        markerName = self._field_module.findFieldByName(marker_name)
        # markerGroup = self._field_module.findFieldByName(marker_group_name)

        self._marker_region = self._region.createRegion()
        marker_fieldmodule = self._marker_region.getFieldmodule()
        temp_nodes = marker_fieldmodule.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        marker_fieldCache = marker_fieldmodule.createFieldcache()
        marker_data_coordinates = findOrCreateFieldCoordinates(marker_fieldmodule, name="marker_data_coordinates",
                                                               components_count=3)
        marker_data_name = findOrCreateFieldStoredString(marker_fieldmodule, name="marker_data_name")
        marker_data_group = findOrCreateFieldGroup(marker_fieldmodule, name="marker")
        marker_data_nodesGroup = marker_data_group.createNodesetGroup(temp_nodes)

        markerTemplateInternal = temp_nodes.createNodetemplate()
        markerTemplateInternal.defineField(marker_data_name)
        markerTemplateInternal.defineField(marker_data_coordinates)
        markerTemplateInternal.setValueNumberOfVersions(marker_data_coordinates, -1, Node.VALUE_LABEL_VALUE, 1)

        for marker_group_name in marker_group_names:
            markerGroup = self._field_module.findFieldByName(marker_group_name)
            markerNodes = None
            if markerGroup.isValid():
                markerGroup = markerGroup.castGroup()
                markerNodes = markerGroup.getNodesetGroup(nodes)

            if markerLocation.isValid() and markerName.isValid():
                with ChangeManager(marker_fieldmodule):
                    marker_coordinates = self._field_module.createFieldEmbedded(self._model_coordinates_field,
                                                                                markerLocation)
                    nodeIter = markerNodes.createNodeiterator()
                    node = nodeIter.next()
                    while node.isValid():
                        marker_node = temp_nodes.createNode(node.getIdentifier(), markerTemplateInternal)
                        marker_data_nodesGroup.addNode(marker_node)

                        marker_fieldCache.setNode(marker_node)
                        field_cache.setNode(node)
                        result, x = marker_coordinates.evaluateReal(field_cache, 3)
                        result = marker_data_coordinates.setNodeParameters(marker_fieldCache, -1,
                                                                           Node.VALUE_LABEL_VALUE, 1, x)
                        if result == RESULT_OK:
                            name = markerName.evaluateString(field_cache)
                            if name:
                                marker_data_name.assignString(marker_fieldCache, name)
                        node = nodeIter.next()

    def _set_model_coordinates_field(self, model_coordinates_field: Field):
        finite_element_field = model_coordinates_field.castFiniteElement()
        assert finite_element_field.isValid() and (finite_element_field.getNumberOfComponents() == 3)
        self._model_coordinates_field = finite_element_field

    def _get_marker_region(self):
        return self._marker_region

