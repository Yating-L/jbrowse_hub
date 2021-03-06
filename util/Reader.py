import os
import json
import shutil
import logging
import codecs


# Internal dependencies
from datatypes.binary.Bam import Bam
from datatypes.binary.BigWig import BigWig
from datatypes.interval.Bed import Bed
from datatypes.interval.BedSimpleRepeats import BedSimpleRepeats
from datatypes.interval.BedSpliceJunctions import BedSpliceJunctions
from datatypes.interval.BlastXml import BlastXml
from datatypes.interval.Gff3 import Gff3
from datatypes.interval.Gtf import Gtf
from datatypes.interval.BigPsl import BigPsl
from datatypes.interval.BedBlatAlignments import BedBlatAlignments
from datatypes.interval.BedBlastAlignments import BedBlastAlignments
from datatypes.interval.Psl import Psl
from datatypes.sequence.Fasta import Fasta
from util import santitizer 

class Reader(object):
    
    DATATYPE_CLASS = [Bam, BigWig, Bed, BedSimpleRepeats, 
        BedSpliceJunctions, BigPsl, BedBlatAlignments, BedBlastAlignments, 
        BlastXml, Gff3, Gtf, Psl, Fasta]

    def __init__(self, input_json_file):
        self.inputFile = input_json_file
        self.args = self.loadJson()
        
    
    def loadJson(self):
        try:
            data_file = codecs.open(self.inputFile, 'r', 'utf-8')   
            return json.load(data_file) 
        except IOError:
            print ("Cannot find JSON file\n")
            exit(1)

    def getToolDir(self):
        try:
            return self.args["tool_directory"]
        except KeyError:
            print ("tool_directory is not defined in the input file!")
            exit(1)

    def getExtFilesPath(self):
        try:
            return self.args["extra_files_path"]
        except KeyError:
            print ("extra_files_path is not defined in the input file!")
            exit(1)

    def getUserEmail(self):
        try:
            return self.args["user_email"]
        except KeyError:
            print ("user_email is not defined in the input file!")
            exit(1)
    
    def getDebugMode(self):
        try:
            return self.args["debug_mode"]
        except KeyError:
            print ("debug_mode is not defined in the input file!")
            exit(1)

    def getTrackType(self):
        try:
            return self.args.get("feature_tracks_type")
        except KeyError:
            print ("feature tracks type is not defined in the input file!")
            exit(1)
    
    def getGenomeName(self):
        genome_name = santitizer.sanitize_name_input(self.args["genome_name"])
        return genome_name
        
    def getRefGenome(self):
        array_inputs_reference_genome = self.args["fasta"]
        input_fasta_file = array_inputs_reference_genome["false_path"]
        input_fasta_file_name = santitizer.sanitize_name_input(array_inputs_reference_genome["name"])
        # Add "fasta" extension because Apollo needs it to create annotation
        refseq_file = os.path.join(os.path.dirname(input_fasta_file), input_fasta_file_name + ".fasta")
        shutil.copyfile(input_fasta_file, refseq_file)
        genome_name = self.getGenomeName()
        reference_genome = Fasta(refseq_file,
                             input_fasta_file_name, genome_name)
        return reference_genome

    def getTracksData(self):
        self.logger = logging.getLogger(__name__)
        all_datatype_dictionary = dict()
        for datatype in self.DATATYPE_CLASS:
            class_name = datatype.__name__
            array_inputs = self.args.get(str(class_name))
            if array_inputs:
                self.logger.debug("Creating %s objects\n", class_name)
                self.logger.debug("array_inputs: %s", array_inputs)
                all_datatype_dictionary.update(self.create_ordered_datatype_objects(datatype, array_inputs))
               
        return all_datatype_dictionary

    def create_ordered_datatype_objects(self, ExtensionClass, array_inputs):
        """
        Function which executes the creation all the necessary files / folders for a special Datatype, for TrackHub
        and update the dictionary of datatype

        :param ExtensionClass:
        :param array_inputs:
        :type ExtensionClass: Datatype
        :type array_inputs: list[string]
        """

        datatype_dictionary = {}

        # TODO: Optimize this double loop
        for input_data in array_inputs:
            input_false_path = input_data["false_path"]
            # if the file is empty, skip the rest
            if os.path.isfile(input_false_path) and os.path.getsize(input_false_path) > 0:
                input_data["name"] = santitizer.sanitize_name_input(input_data["name"])
                extensionObject = ExtensionClass(input_false_path, input_data)
                extensionObject.generateCustomTrack()
                datatype_dictionary.update({input_data["order_index"]: extensionObject})
                self.logger.debug("%s object: %s has been created", ExtensionClass, input_data["name"])
            else:
                self.logger.info("The input file: %s is empty, skip creating the track for this data", input_data["name"])
        return datatype_dictionary

    
        


