
"""
MAP Client Plugin Step
"""
import csv
import json
import os

from PySide6 import QtCore, QtGui, QtWidgets

from cmlibs.utils.zinc.general import ChangeManager
from cmlibs.zinc.context import Context

from mapclient.mountpoints.workflowstep import WorkflowStepMountPoint
from mapclientplugins.organinserterstep.configuredialog import ConfigureDialog
from mapclientplugins.organinserterstep.organinserterwidget import OrganInserterWidget

from scaffoldfitter.fitter import Fitter
from scaffoldfitter.fitterstepalign import FitterStepAlign
from scaffoldfitter.fitterstepfit import FitterStepFit
from mapclientplugins.organinserterstep.organinsertermodel import OrganInserter

class OrganInserterStep(WorkflowStepMountPoint):
    """
    Skeleton step which is intended to be a helpful starting point
    for new steps.
    """

    def __init__(self, location):
        super(OrganInserterStep, self).__init__('Organ Inserter', location)
        self._view = None
        self._configured = False  # A step cannot be executed until it has been configured.
        self._category = 'Registration'
        # Add any other initialisation code here:
        self._icon = QtGui.QImage(':/organinserterstep/images/registration.png')
        # Ports:
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#uses',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'))
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#uses-list-of',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'))
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#provides',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'))
        # Port data:
        self._port0_inputZincModelFile = None  # http://physiomeproject.org/workflow/1.0/rdf-schema#file_location
        self._port1_inputZincDataFile = None  # http://physiomeproject.org/workflow/1.0/rdf-schema#file_location
        self._port2_output_marker_data_file = None  # http://physiomeproject.org/workflow/1.0/rdf-schema#file_location
        # Config:
        self._config = {'identifier': ''}

        self._organ_inserter = None

    def execute(self):
        """
        Add your code here that will kick off the execution of the step.
        Make sure you call the _doneExecution() method when finished.  This method
        may be connected up to a button in a widget for example.
        """
        # Put your execute step code here before calling the '_doneExecution' method.
        print(self._port0_inputZincModelFile, self._port1_inputZincDataFile)
        self._view = OrganInserterWidget(self._port0_inputZincModelFile, self._port1_inputZincDataFile,
                                             self._location)
        self._setCurrentWidget(self._view)
        # self._organ_inserter = OrganInserter(self._port0_inputZincModelFile, self._port1_inputZincDataFile,
        #                                      self._location)
        # self._port2_output_marker_data_file = self._organ_inserter.get_output_file_name()

        self._view.register_done_execution(self.doneButtonClicked)

    def doneButtonClicked(self, organ_file_dict):
        # self.write_annotations(self._location)
        input_list = list(organ_file_dict.values())
        input_list.remove(organ_file_dict['whole body'])
        whole_body_model = organ_file_dict['whole body']
        for i in input_list:
            self._fitter = Fitter(whole_body_model, i)
            self._fitter.load()
            alig  = FitterStepAlign()
            alig.setAlignMarkers(True)
            alig.setAlignGroups(True)
            self._fitter.addFitterStep(alig)

            _currentFitterStep = FitterStepFit()
            self._fitter.addFitterStep(_currentFitterStep)
            _currentFitterStep.setGroupStrainPenalty(None, [0.001])
            _currentFitterStep.setGroupCurvaturePenalty(None, [200.0])
            _currentFitterStep.setGroupDataWeight(None, 1000.0)

            self._output_filenames = []
            fitterSteps = self._fitter.getFitterSteps()
            print(fitterSteps)
            self._fitter.run(endStep=None, modelFileNameStem=self._location)
            self._fitter.writeModel(self._location + "/fitted.exf")
            whole_body_model = self._location + "/fitted.exf"
        # self._organ_inserter = OrganInserter(whole_body_model, input_list,
        #                                      self._location)
        self._port2_output_marker_data_file = self._location + "/fitted.exf"
        self._doneExecution()

    def get_output_file_name(self):
        return self._output_filenames

    def get_organ_name(self, filename):
        organsList = ['lung', 'heart', 'brainstem', 'stomach', 'bladder']
        filename_base = os.path.basename(filename).split('.')[0]
        for organ_name in organsList:
            if organ_name in filename_base.lower():
                return organ_name
        else:
            return filename_base

    def write_annotations(self, output_directory):
        DOI = ["https://doi.org/10.26275/yibc-wyu2", "https://doi.org/10.26275/dqpf-gqdt",
               "https://doi.org/10.26275/rets-qdch", "https://doi.org/10.26275/dqpf-gqdt",
               "https://doi.org/10.26275/yum2-z4uf", "https://doi.org/10.26275/xq3h-ba2b", "colon"]
        organ_names = ['whole-body']
        for filename in self._input_data_files:
            organ_names.append(self.get_organ_name(filename))

        annotation_file = os.path.join(output_directory, 'organinserter_annotations.csv')
        with open(annotation_file, 'w', newline='') as fout:
            writer = csv.writer(fout)
            writer.writerow(['Organ name', 'Source', 'File name', 'Transformed file name'])
            writer.writerow([organ_names[0], DOI[0], 'whole_body.exf', 'whole_body.exf'])
            for c, filename in enumerate(self._input_data_files):
                filenamebase = os.path.basename(filename)
                writer.writerow([organ_names[c + 1], DOI[c + 1], filenamebase,
                                 filenamebase.split('.')[0] + '_transfromed_fit1.exf'])

    def add_organ_group(self, filename):
        context = Context('organGroup')
        region = context.createRegion()
        region.readFile(filename)
        field_module = region.getFieldmodule()
        mesh = field_module.findMeshByDimension(3)
        with ChangeManager(field_module):
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
            # sir.setResourceFieldNames(srm, fieldNames)
            region.write(sir)
            region.writeFile(filename)


    def setPortData(self, index, dataIn):
        """
        Add your code here that will set the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        uses port for this step then the index can be ignored.

        :param index: Index of the port to return.
        :param dataIn: The data to set for the port at the given index.
        """
        if index == 0:
            self._port0_inputZincModelFile = dataIn  # http://physiomeproject.org/workflow/1.0/rdf-schema#file_location
        elif index == 1:
            self._port1_inputZincDataFile = dataIn  # http://physiomeproject.org/workflow/1.0/rdf-schema#file_location

    def getPortData(self, index):
        """
        Add your code here that will return the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        provides port for this step then the index can be ignored.

        :param index: Index of the port to return.
        """
        # files = []
        # for file in self._port2_output_marker_data_file:
        #     files.append(os.path.realpath(os.path.join(self._location, file)))
        # return files  # http://physiomeproject.org/workflow/1.0/rdf-schema#multiple_file_locations
        return self._port2_output_marker_data_file  # http://physiomeproject.org/workflow/1.0/rdf-schema#file_location

    def configure(self):
        """
        This function will be called when the configure icon on the step is
        clicked.  It is appropriate to display a configuration dialog at this
        time.  If the conditions for the configuration of this step are complete
        then set:
            self._configured = True
        """
        dlg = ConfigureDialog(self._main_window)
        dlg.identifierOccursCount = self._identifierOccursCount
        dlg.setConfig(self._config)
        dlg.validate()
        dlg.setModal(True)

        if dlg.exec_():
            self._config = dlg.getConfig()

        self._configured = dlg.validate()
        self._configuredObserver()

    def getIdentifier(self):
        """
        The identifier is a string that must be unique within a workflow.
        """
        return self._config['identifier']

    def setIdentifier(self, identifier):
        """
        The framework will set the identifier for this step when it is loaded.
        """
        self._config['identifier'] = identifier

    def serialize(self):
        """
        Add code to serialize this step to string.  This method should
        implement the opposite of 'deserialize'.
        """
        return json.dumps(self._config, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def deserialize(self, string):
        """
        Add code to deserialize this step from string.  This method should
        implement the opposite of 'serialize'.

        :param string: JSON representation of the configuration in a string.
        """
        self._config.update(json.loads(string))

        d = ConfigureDialog()
        d.identifierOccursCount = self._identifierOccursCount
        d.setConfig(self._config)
        self._configured = d.validate()
