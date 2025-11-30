#include "dofbot_moveit/dofbot_kinemarics.h"
#include <urdf/model.h>
#include <kdl_parser/kdl_parser.hpp>
#include <fstream>

bool Dofbot::dofbot_getFK(const char *urdf_file, vector<double> &joints, vector<double> &currentPos) {
    KDL::Tree tree;
    if (!kdl_parser::treeFromFile(urdf_file, tree)) {
        cerr << "Failed to construct kdl tree from urdf file: " << urdf_file << endl;
        return false;
    }

    KDL::Chain chain;
    // Assuming base_link to link5 or similar. Need to check URDF for end effector link name.
    // Based on URDF analysis: base_link -> arm_link5 (or tool link?)
    // The URDF has arm_link1...arm_link5. And then gripper links.
    // Let's assume the chain is from base_link to arm_link5 for now, or check what the original code might have expected.
    // Given the 5 joints input, it's likely a 5 DOF arm.
    if (!tree.getChain("base_link", "arm_link5", chain)) {
        cerr << "Failed to get chain from base_link to arm_link5" << endl;
        return false;
    }

    if (joints.size() != chain.getNrOfJoints()) {
        cerr << "Joints size mismatch. Expected " << chain.getNrOfJoints() << ", got " << joints.size() << endl;
        return false;
    }

    KDL::JntArray q(chain.getNrOfJoints());
    for (unsigned int i = 0; i < chain.getNrOfJoints(); ++i) {
        q(i) = joints[i];
    }

    KDL::ChainFkSolverPos_recursive fk_solver(chain);
    KDL::Frame p_out;
    if (fk_solver.JntToCart(q, p_out) < 0) {
        cerr << "FK solver failed" << endl;
        return false;
    }

    currentPos.clear();
    currentPos.push_back(p_out.p.x());
    currentPos.push_back(p_out.p.y());
    currentPos.push_back(p_out.p.z());

    double roll, pitch, yaw;
    p_out.M.GetRPY(roll, pitch, yaw);
    currentPos.push_back(roll);
    currentPos.push_back(pitch);
    currentPos.push_back(yaw);

    return true;
}

bool Dofbot::dofbot_getIK(const char *urdf_file, vector<double> &targetXYZ, vector<double> &targetRPY, vector<double> &outjoints) {
    KDL::Tree tree;
    if (!kdl_parser::treeFromFile(urdf_file, tree)) {
        cerr << "Failed to construct kdl tree" << endl;
        return false;
    }

    KDL::Chain chain;
    if (!tree.getChain("base_link", "arm_link5", chain)) {
        cerr << "Failed to get chain" << endl;
        return false;
    }

    KDL::ChainIkSolverPos_LMA ik_solver(chain);
    
    KDL::JntArray q_init(chain.getNrOfJoints());
    // Initialize with zeros or random? LMA is local.
    for(unsigned int i=0; i<chain.getNrOfJoints(); ++i) q_init(i) = 0.0;

    KDL::Frame p_in;
    p_in.p = KDL::Vector(targetXYZ[0], targetXYZ[1], targetXYZ[2]);
    p_in.M = KDL::Rotation::RPY(targetRPY[0], targetRPY[1], targetRPY[2]);

    KDL::JntArray q_out(chain.getNrOfJoints());
    if (ik_solver.CartToJnt(q_init, p_in, q_out) < 0) {
        cerr << "IK solver failed" << endl;
        return false;
    }

    outjoints.clear();
    for (unsigned int i = 0; i < chain.getNrOfJoints(); ++i) {
        outjoints.push_back(q_out(i));
    }

    return true;
}
