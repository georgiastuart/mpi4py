from mpi4py import MPI
import mpiunittest as unittest
import arrayimpl

class TestMessage(unittest.TestCase):

    def testMessageNull(self):
        null = MPI.MESSAGE_NULL
        self.assertFalse(null)
        null2 = MPI.Message()
        self.assertEqual(null, null2)
        null3 = MPI.Message(null)
        self.assertEqual(null, null3)

    def testMessageNoProc(self):
        #
        noproc = MPI.MESSAGE_NO_PROC
        self.assertTrue(noproc)
        noproc.Recv(None)
        self.assertTrue(noproc)
        noproc.Irecv(None).Wait()
        self.assertTrue(noproc)
        #
        noproc2 = MPI.Message(MPI.MESSAGE_NO_PROC)
        self.assertTrue(noproc2)
        self.assertEqual(noproc2, noproc)
        self.assertNotEqual(noproc, MPI.MESSAGE_NULL)
        #
        message = MPI.Message(MPI.MESSAGE_NO_PROC)
        message.Recv(None)
        self.assertEqual(message, MPI.MESSAGE_NULL)
        #
        message = MPI.Message(MPI.MESSAGE_NO_PROC)
        request = message.Irecv(None)
        self.assertEqual(message, MPI.MESSAGE_NULL)
        self.assertNotEqual(request, MPI.REQUEST_NULL)
        request.Wait()
        self.assertEqual(request, MPI.REQUEST_NULL)


class BaseTestP2PMatched(object):

    COMM = MPI.COMM_NULL

    def testIMProbe(self):
        comm = self.COMM.Dup()
        try:
            m = comm.Improbe()
            self.assertEqual(m, None)
            m = comm.Improbe(MPI.ANY_SOURCE)
            self.assertEqual(m, None)
            m = comm.Improbe(MPI.ANY_SOURCE, MPI.ANY_TAG)
            self.assertEqual(m, None)
            status = MPI.Status()
            m = comm.Improbe(MPI.ANY_SOURCE, MPI.ANY_TAG, status)
            self.assertEqual(m, None)
            self.assertEqual(status.source, MPI.ANY_SOURCE)
            self.assertEqual(status.tag,    MPI.ANY_TAG)
            self.assertEqual(status.error,  MPI.SUCCESS)
            m = MPI.Message.Iprobe(comm)
            self.assertEqual(m, None)
        finally:
            comm.Free()

    def testProbeRecv(self):
        comm = self.COMM
        size = comm.Get_size()
        rank = comm.Get_rank()
        for array in arrayimpl.ArrayTypes:
            for typecode in arrayimpl.TypeMap:
                for s in range(0, size+1):
                    sbuf = array( s, typecode, s)
                    rbuf = array(-1, typecode, s)
                    if size == 1:
                        m = comm.Improbe(0, 0)
                        self.assertEqual(m, None)
                        sr = comm.Isend(sbuf.as_mpi(), 0, 0)
                        m = comm.Mprobe(0, 0)
                        self.assertTrue(isinstance(m, MPI.Message))
                        self.assertTrue(m)
                        n = comm.Improbe(0, 0)
                        self.assertEqual(n, None)
                        rr = m.Irecv(rbuf.as_raw())
                        self.assertFalse(m)
                        self.assertTrue(rr)
                        MPI.Request.Waitall([sr,rr])
                        self.assertFalse(rr)
                        #
                        r = comm.Isend(sbuf.as_mpi(), 0, 0)
                        m = MPI.Message.Probe(comm, 0, 0)
                        self.assertTrue(isinstance(m, MPI.Message))
                        self.assertTrue(m)
                        n = MPI.Message.Iprobe(comm, 0, 0)
                        self.assertEqual(n, None)
                        m.Recv(rbuf.as_raw())
                        self.assertFalse(m)
                        r.Wait()
                        #
                        r = comm.Isend(sbuf.as_mpi(), 0, 0)
                        m = MPI.Message.Iprobe(comm, 0, 0)
                        self.assertTrue(isinstance(m, MPI.Message))
                        self.assertTrue(m)
                        n = MPI.Message.Iprobe(comm, 0, 0)
                        self.assertEqual(n, None)
                        m.Recv(rbuf.as_raw())
                        self.assertFalse(m)
                        r.Wait()
                        #
                        r = comm.Isend(sbuf.as_mpi(), 0, 0)
                        m = comm.Mprobe(0, 0)
                        self.assertTrue(isinstance(m, MPI.Message))
                        self.assertTrue(m)
                        n = comm.Improbe(0, 0)
                        self.assertEqual(n, None)
                        m.Recv(rbuf.as_raw())
                        self.assertFalse(m)
                        r.Wait()
                    elif rank == 0:
                        comm.Send(sbuf.as_mpi(), 1, 0)
                        m = comm.Mprobe(1, 0)
                        self.assertTrue(m)
                        n = comm.Improbe(0, 0)
                        self.assertEqual(n, None)
                        m.Recv(rbuf.as_raw())
                        self.assertFalse(m)
                        #
                        comm.Send(sbuf.as_mpi(), 1, 1)
                        m = None
                        while not m:
                            m = comm.Improbe(1, 1)
                        m.Irecv(rbuf.as_raw()).Wait()
                        n = comm.Improbe(1, 1)
                        self.assertEqual(n, None)
                    elif rank == 1:
                        m = comm.Mprobe(0, 0)
                        self.assertTrue(m)
                        n = comm.Improbe(1, 0)
                        self.assertEqual(n, None)
                        m.Recv(rbuf.as_raw())
                        self.assertFalse(m)
                        comm.Send(sbuf.as_mpi(), 0, 0)
                        #
                        m = None
                        while not m:
                            m = comm.Improbe(0, 1)
                        m.Irecv(rbuf.as_mpi()).Wait()
                        comm.Send(sbuf.as_mpi(), 0, 1)
                        n = comm.Improbe(0, 1)
                        self.assertEqual(n, None)
                    else:
                        rbuf = sbuf

                    for value in rbuf:
                        self.assertEqual(value, s)

class TestP2PMatchedSelf(BaseTestP2PMatched, unittest.TestCase):
    COMM = MPI.COMM_SELF

class TestP2PMatchedWorld(BaseTestP2PMatched, unittest.TestCase):
    COMM = MPI.COMM_WORLD

class TestP2PMatchedSelfDup(BaseTestP2PMatched, unittest.TestCase):
    def setUp(self):
        self.COMM = MPI.COMM_SELF.Dup()
    def tearDown(self):
        self.COMM.Free()

class TestP2PMatchedWorldDup(BaseTestP2PMatched, unittest.TestCase):
    def setUp(self):
        self.COMM = MPI.COMM_WORLD.Dup()
    def tearDown(self):
        self.COMM.Free()


if MPI.MESSAGE_NULL == MPI.MESSAGE_NO_PROC:
    del TestMessage
    del TestP2PMatchedSelf
    del TestP2PMatchedWorld
    del TestP2PMatchedSelfDup
    del TestP2PMatchedWorldDup
else:
    name, version = MPI.get_vendor()
    if name == 'Open MPI':
        if MPI.COMM_WORLD.Get_size() > 1:
            del TestP2PMatchedSelfDup
            del TestP2PMatchedWorldDup


if __name__ == '__main__':
    unittest.main()
